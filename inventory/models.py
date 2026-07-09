from django.db import models


class ProductType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT, related_name='products')
    company_name = models.CharField(max_length=150)
    product_title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(
        default=5,
        help_text='Show a low-stock warning once quantity falls to or below this number.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product_title']
        constraints = [
            models.CheckConstraint(check=models.Q(price__gte=0), name='product_price_non_negative'),
        ]

    def __str__(self):
        return f'{self.product_title} ({self.company_name})'

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level
