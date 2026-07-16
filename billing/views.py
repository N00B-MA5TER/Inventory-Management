from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.decorators import staff_required, superadmin_required
from accounts.models import ActionLog
from billing.forms import OrderCustomerForm
from billing.models import Bill, BillItem, Order, OrderItem
from billing.reports import daily_summary_context, monthly_summary_context
from inventory.models import Product
from inventory.queries import browsable_products

CART_SESSION_KEY = 'cart'


def _get_cart(request):
    return request.session.setdefault(CART_SESSION_KEY, {})


def _cart_items(request):
    cart = _get_cart(request)
    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.in_bulk(product_ids)
    items = []
    for pid_str, qty in cart.items():
        product = products.get(int(pid_str))
        if product:
            items.append({'product': product, 'quantity': qty})
    return items


def _deduct_stock(order):
    for item in order.items.select_related('product'):
        if item.product.tracks_stock:
            item.product.stock_quantity = max(0, item.product.stock_quantity - item.quantity)
            item.product.save(update_fields=['stock_quantity'])


@login_required
def order_build(request):
    query = request.GET.get('q', '').strip()
    active_type = request.GET.get('type', Product.ProductType.TOOLS)
    if active_type not in Product.ProductType.values:
        active_type = Product.ProductType.TOOLS

    products = browsable_products(active_type, search=query)
    cart_items = _cart_items(request)
    cart_total_quantity = sum(item['quantity'] for item in cart_items)

    return render(request, 'billing/order_build.html', {
        'products': products,
        'query': query,
        'active_type': active_type,
        'product_types': Product.ProductType.choices,
        'cart_items': cart_items,
        'cart_total_quantity': cart_total_quantity,
        'customer_form': OrderCustomerForm(),
        'show_exact_stock': request.user.profile.is_admin_or_above,
    })


@login_required
def cart_add(request, pk):
    redirect_type = request.POST.get('type', Product.ProductType.TOOLS) if request.method == 'POST' else Product.ProductType.TOOLS

    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
        quantity = max(1, quantity)

        if product.tracks_stock:
            cart = _get_cart(request)
            already_in_cart = cart.get(str(product.pk), 0)
            if already_in_cart + quantity > product.stock_quantity:
                available = max(0, product.stock_quantity - already_in_cart)
                messages.error(request, f'Only {available} more x {product.product_title} available.')
                return redirect(f"{reverse('billing:order_build')}?type={redirect_type}")

        cart = _get_cart(request)
        cart[str(product.pk)] = cart.get(str(product.pk), 0) + quantity
        request.session.modified = True
        messages.success(request, f'Added {quantity} x {product.product_title} to the order.')

    return redirect(f"{reverse('billing:order_build')}?type={redirect_type}")


@login_required
def cart_remove(request, pk):
    if request.method == 'POST':
        cart = _get_cart(request)
        cart.pop(str(pk), None)
        request.session.modified = True
    return redirect('billing:order_build')


@login_required
def order_place(request):
    if request.method != 'POST':
        return redirect('billing:order_build')

    cart_items = _cart_items(request)
    if not cart_items:
        messages.error(request, 'Add at least one item before placing the order.')
        return redirect('billing:order_build')

    is_staff_order = request.user.profile.is_admin_or_above

    customer_form = OrderCustomerForm(request.POST)
    order = customer_form.save(commit=False) if customer_form.is_valid() else Order()
    order.created_by = request.user

    if is_staff_order:
        order.status = Order.Status.APPROVED
        order.reviewed_by = request.user
        order.reviewed_at = timezone.now()
    else:
        order.status = Order.Status.PENDING

    order.save()

    for item in cart_items:
        OrderItem.objects.create(order=order, product=item['product'], quantity=item['quantity'])

    if is_staff_order:
        _deduct_stock(order)

    request.session[CART_SESSION_KEY] = {}
    request.session.modified = True

    ActionLog.objects.create(user=request.user, action=f'Placed order #{order.id}')
    if is_staff_order:
        messages.success(request, f'Order #{order.id} placed.')
    else:
        messages.success(request, f'Order #{order.id} placed — waiting for approval.')
    return redirect('billing:order_detail', pk=order.pk)


def _can_view_order(request, order):
    return order.created_by_id == request.user.id or request.user.profile.is_admin_or_above


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    if not _can_view_order(request, order):
        return HttpResponseForbidden('You cannot view this order.')
    return render(request, 'billing/order_detail.html', {
        'order': order,
        'can_review': request.user.profile.is_admin_or_above,
        'can_decline': request.user.profile.is_superadmin,
    })


@login_required
def my_orders(request):
    orders = Order.objects.filter(created_by=request.user).prefetch_related('items__product')
    return render(request, 'billing/my_orders.html', {'orders': orders})


@staff_required
def order_approval_queue(request):
    pending = Order.objects.filter(status=Order.Status.PENDING).select_related('created_by').prefetch_related('items__product')
    return render(request, 'billing/order_approval_queue.html', {
        'pending': pending,
        'can_decline': request.user.profile.is_superadmin,
    })


@staff_required
def order_approve(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk, status=Order.Status.PENDING)
    if request.method == 'POST':
        insufficient = [
            item.product.product_title for item in order.items.select_related('product')
            if item.product.tracks_stock and item.quantity > item.product.stock_quantity
        ]
        if insufficient:
            messages.error(request, f"Not enough stock for: {', '.join(insufficient)}. Cannot approve.")
        else:
            _deduct_stock(order)
            order.status = Order.Status.APPROVED
            order.reviewed_by = request.user
            order.reviewed_at = timezone.now()
            order.save()

            ActionLog.objects.create(user=request.user, action=f'Approved order #{order.id}')
            messages.success(request, f'Order #{order.id} approved.')

    return redirect(request.POST.get('next') or 'billing:order_approval_queue')


@superadmin_required
def order_decline(request, pk):
    order = get_object_or_404(Order, pk=pk, status=Order.Status.PENDING)
    if request.method == 'POST':
        order.status = Order.Status.DECLINED
        order.reviewed_by = request.user
        order.reviewed_at = timezone.now()
        order.save()

        ActionLog.objects.create(user=request.user, action=f'Declined order #{order.id}')
        messages.success(request, f'Order #{order.id} declined.')

    return redirect(request.POST.get('next') or 'billing:order_approval_queue')


@staff_required
def bill_create(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    if order.has_bill:
        return redirect('billing:bill_detail', pk=order.bill.pk)
    if order.status != Order.Status.APPROVED:
        messages.error(request, 'Only approved orders can be billed.')
        return redirect('billing:order_detail', pk=order.pk)

    if request.method == 'POST':
        bill = Bill(
            order=order,
            bill_number=f'BILL-{order.id}-{int(timezone.now().timestamp())}',
            created_by=request.user,
        )
        bill.save()

        for item in order.items.all():
            raw_amount = request.POST.get(f'amount_{item.id}', '0')
            try:
                amount = Decimal(raw_amount)
            except InvalidOperation:
                amount = Decimal('0.00')
            BillItem.objects.create(bill=bill, product=item.product, quantity=item.quantity, amount=amount)

        ActionLog.objects.create(user=request.user, action=f'Generated bill {bill.bill_number} for order #{order.id}')
        messages.success(request, f'Bill {bill.bill_number} created.')
        return redirect('billing:bill_detail', pk=bill.pk)

    suggested = [
        {'item': item, 'suggested_amount': (item.product.price * item.quantity)}
        for item in order.items.all()
    ]
    return render(request, 'billing/bill_form.html', {'order': order, 'suggested': suggested})


@login_required
def bill_detail(request, pk):
    bill = get_object_or_404(Bill.objects.prefetch_related('items__product').select_related('order'), pk=pk)
    if not _can_view_order(request, bill.order):
        return HttpResponseForbidden('You cannot view this bill.')
    return render(request, 'billing/bill_detail.html', {'bill': bill})


@superadmin_required
def daily_summary(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            selected_date = timezone.localdate()
    else:
        selected_date = timezone.localdate()

    context = daily_summary_context(selected_date)
    context['prev_date'] = selected_date - timedelta(days=1)
    context['next_date'] = selected_date + timedelta(days=1)
    return render(request, 'billing/daily_summary.html', context)


@superadmin_required
def monthly_summary(request):
    today = timezone.localdate()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    context = monthly_summary_context(year, month)
    prev_month = month - 1 or 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year
    context.update({
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
    })
    return render(request, 'billing/monthly_summary.html', context)
