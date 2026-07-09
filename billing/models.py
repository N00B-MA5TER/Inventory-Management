from django.conf import settings
from django.db import models

from inventory.models import Product


class Order(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    customer_name = models.CharField(max_length=150, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.id} - {self.customer_name or "Walk-in"}'

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def has_bill(self):
        return hasattr(self, 'bill')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.quantity} x {self.product.product_title}'


class Bill(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='bill')
    bill_number = models.CharField(max_length=50, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bills_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.bill_number

    @property
    def total_amount(self):
        return sum(item.amount for item in self.items.all())


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='bill_items')
    quantity = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='Editable total charge for this item')

    def __str__(self):
        return f'{self.quantity} x {self.product.product_title} = {self.amount}'
