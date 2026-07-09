from django import forms

from inventory.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_type',
            'product_title',
            'company_name',
            'description',
            'price',
            'stock_quantity',
            'reorder_level',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'product_title': 'Item Name',
            'company_name': 'Company / Brand',
            'stock_quantity': 'Quantity in Stock',
            'reorder_level': 'Warn Me When Stock Falls To',
        }
