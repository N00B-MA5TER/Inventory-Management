from django import forms

from inventory.models import Product


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
        help_texts = {
            'stock_quantity': 'Not used for Services — services are always available.',
        }


class RestockItemForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.filter(product_type__in=[
        Product.ProductType.TOOLS, Product.ProductType.SPARE_PARTS,
    ]), label='Item')
    quantity_to_add = forms.IntegerField(min_value=1, label='Quantity to Add')
