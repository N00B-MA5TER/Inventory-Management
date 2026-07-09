from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import ActionLog
from inventory.forms import ProductForm
from inventory.models import Product


@login_required
def product_list(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.select_related('product_type')

    if query:
        products = products.filter(
            Q(product_title__icontains=query) | Q(company_name__icontains=query)
        )

    return render(request, 'inventory/product_list.html', {
        'products': products,
        'query': query,
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
