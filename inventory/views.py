from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import staff_required, superadmin_required
from accounts.models import ActionLog
from inventory.forms import ProductForm, RestockItemForm
from inventory.models import Product, StockOnboardingItem, StockOnboardingRequest
from inventory.queries import browsable_products, filter_options

RESTOCK_CART_SESSION_KEY = 'restock_cart'


def _get_restock_cart(request):
    return request.session.setdefault(RESTOCK_CART_SESSION_KEY, {})


def _restock_cart_items(request):
    cart = _get_restock_cart(request)
    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.in_bulk(product_ids)
    items = []
    for pid_str, qty in cart.items():
        product = products.get(int(pid_str))
        if product:
            items.append({'product': product, 'quantity': qty})
    return items


@staff_required
def product_list(request):
    query = request.GET.get('q', '').strip()
    active_type = request.GET.get('type', Product.ProductType.TOOLS)
    if active_type not in Product.ProductType.values:
        active_type = Product.ProductType.TOOLS

    company = request.GET.get('company', '').strip()
    vehicle_make = request.GET.get('vehicle_make', '').strip()
    vehicle_model = request.GET.get('vehicle_model', '').strip()

    products = browsable_products(
        active_type, search=query, company=company, vehicle_make=vehicle_make, vehicle_model=vehicle_model,
    )

    return render(request, 'inventory/product_list.html', {
        'products': products,
        'query': query,
        'active_type': active_type,
        'product_types': Product.ProductType.choices,
        'show_exact_stock': True,
        'filter_options': filter_options(active_type, company=company, vehicle_make=vehicle_make),
        'selected_company': company,
        'selected_vehicle_make': vehicle_make,
        'selected_vehicle_model': vehicle_model,
    })


@staff_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            ActionLog.objects.create(user=request.user, action=f'Added item "{product.product_title}"')
            messages.success(request, f'"{product.product_title}" was added.')
            return redirect('inventory:product_list')
    else:
        form = ProductForm()

    return render(request, 'inventory/product_form.html', {'form': form, 'is_edit': False})


@staff_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            ActionLog.objects.create(user=request.user, action=f'Updated item "{product.product_title}"')
            messages.success(request, f'"{product.product_title}" was updated.')
            return redirect('inventory:product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'inventory/product_form.html', {'form': form, 'is_edit': True, 'product': product})


@staff_required
def stock_onboarding_build(request):
    cart_items = _restock_cart_items(request)
    return render(request, 'inventory/stock_onboarding_form.html', {
        'form': RestockItemForm(),
        'cart_items': cart_items,
    })


@staff_required
def stock_onboarding_cart_add(request):
    if request.method == 'POST':
        form = RestockItemForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity_to_add']
            cart = _get_restock_cart(request)
            cart[str(product.pk)] = cart.get(str(product.pk), 0) + quantity
            request.session.modified = True
            messages.success(request, f'Added {quantity} x {product.product_title} to the list.')
        else:
            messages.error(request, 'Please pick an item and a valid quantity.')

    return redirect('inventory:stock_onboarding_build')


@staff_required
def stock_onboarding_cart_remove(request, pk):
    if request.method == 'POST':
        cart = _get_restock_cart(request)
        cart.pop(str(pk), None)
        request.session.modified = True
    return redirect('inventory:stock_onboarding_build')


@staff_required
def stock_onboarding_submit(request):
    if request.method != 'POST':
        return redirect('inventory:stock_onboarding_build')

    cart_items = _restock_cart_items(request)
    if not cart_items:
        messages.error(request, 'Add at least one item before submitting.')
        return redirect('inventory:stock_onboarding_build')

    onboarding_request = StockOnboardingRequest.objects.create(submitted_by=request.user)
    for item in cart_items:
        StockOnboardingItem.objects.create(
            request=onboarding_request, product=item['product'], quantity_to_add=item['quantity']
        )

    request.session[RESTOCK_CART_SESSION_KEY] = {}
    request.session.modified = True

    ActionLog.objects.create(
        user=request.user,
        action=f'Submitted stock onboarding request #{onboarding_request.id} for approval',
    )
    messages.success(request, 'Your restock request was submitted for approval.')
    return redirect('inventory:product_list')


@superadmin_required
def stock_onboarding_queue(request):
    pending = StockOnboardingRequest.objects.filter(
        status=StockOnboardingRequest.Status.PENDING
    ).select_related('submitted_by').prefetch_related('items__product')
    history = StockOnboardingRequest.objects.exclude(
        status=StockOnboardingRequest.Status.PENDING
    ).select_related('submitted_by', 'reviewed_by').prefetch_related('items__product')[:20]

    return render(request, 'inventory/stock_onboarding_queue.html', {
        'pending': pending,
        'history': history,
    })


@superadmin_required
def stock_onboarding_approve(request, pk):
    onboarding_request = get_object_or_404(
        StockOnboardingRequest, pk=pk, status=StockOnboardingRequest.Status.PENDING
    )
    if request.method == 'POST':
        for item in onboarding_request.items.select_related('product'):
            product = item.product
            product.stock_quantity += item.quantity_to_add
            product.save(update_fields=['stock_quantity'])

        onboarding_request.status = StockOnboardingRequest.Status.APPROVED
        onboarding_request.reviewed_by = request.user
        onboarding_request.reviewed_at = timezone.now()
        onboarding_request.save()

        ActionLog.objects.create(
            user=request.user,
            action=f'Approved stock onboarding request #{onboarding_request.id}',
        )
        messages.success(request, f'Request #{onboarding_request.id} approved and stock updated.')

    return redirect('inventory:stock_onboarding_queue')


@superadmin_required
def stock_onboarding_reject(request, pk):
    onboarding_request = get_object_or_404(
        StockOnboardingRequest, pk=pk, status=StockOnboardingRequest.Status.PENDING
    )
    if request.method == 'POST':
        onboarding_request.status = StockOnboardingRequest.Status.REJECTED
        onboarding_request.reviewed_by = request.user
        onboarding_request.reviewed_at = timezone.now()
        onboarding_request.save()

        ActionLog.objects.create(
            user=request.user,
            action=f'Rejected stock onboarding request #{onboarding_request.id}',
        )
        messages.success(request, f'Request #{onboarding_request.id} was rejected.')

    return redirect('inventory:stock_onboarding_queue')
