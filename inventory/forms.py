from django import forms
from django.forms import inlineformset_factory

from inventory.models import Product, StockOnboardingItem, StockOnboardingRequest


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_type',
            'product_title',
            'company_name',
            'price',
            'stock_quantity',
        ]
        labels = {
            'product_title': 'Item Name',
            'company_name': 'Company / Brand',
            'stock_quantity': 'Quantity in Stock',
        }


class StockOnboardingItemForm(forms.ModelForm):
    class Meta:
        model = StockOnboardingItem
        fields = ['product', 'quantity_to_add']
        labels = {
            'quantity_to_add': 'Quantity to Add',
        }


StockOnboardingItemFormSet = inlineformset_factory(
    StockOnboardingRequest,
    StockOnboardingItem,
    form=StockOnboardingItemForm,
    extra=3,
    can_delete=False,
    min_num=1,
    validate_min=True,
)
