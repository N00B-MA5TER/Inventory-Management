from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import superadmin_required
from accounts.models import ActionLog
from inventory.forms import ProductForm, StockOnboardingItemFormSet
from inventory.models import Product, StockOnboardingRequest
from inventory.queries import browsable_products


@login_required
def product_list(request):
    query = request.GET.get('q', '').strip()
    active_type = request.GET.get('type', Product.ProductType.TOOLS)
    if active_type not in Product.ProductType.values:
        active_type = Product.ProductType.TOOLS

    products = browsable_products(active_type, search=query)

    return render(request, 'inventory/product_list.html', {
        'products': products,
        'query': query,
        'active_type': active_type,
        'product_types': Product.ProductType.choices,
    })


@login_required
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


@login_required
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


@login_required
def stock_onboarding_create(request):
    if request.method == 'POST':
        onboarding_request = StockOnboardingRequest(submitted_by=request.user)
        formset = StockOnboardingItemFormSet(request.POST, instance=onboarding_request)
        if formset.is_valid():
            onboarding_request.save()
            formset.instance = onboarding_request
            formset.save()
            ActionLog.objects.create(
                user=request.user,
                action=f'Submitted stock onboarding request #{onboarding_request.id} for approval',
            )
            messages.success(request, 'Your restock request was submitted for approval.')
            return redirect('inventory:product_list')
    else:
        formset = StockOnboardingItemFormSet()

    return render(request, 'inventory/stock_onboarding_form.html', {'formset': formset})


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
