from django import forms

from billing.models import Order


class OrderCustomerForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_phone']
        labels = {
            'customer_name': 'Customer Name (optional)',
            'customer_phone': 'Customer Phone (optional)',
        }
