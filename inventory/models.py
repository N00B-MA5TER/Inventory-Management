from django.conf import settings
from django.db import models

RESTOCK_THRESHOLD = 3


class Product(models.Model):
    class ProductType(models.TextChoices):
        TOOLS = 'tools', 'Tools'
        SPARE_PARTS = 'spare_parts', 'Spare Parts'
        SERVICES = 'services', 'Services'

    product_type = models.CharField(max_length=20, choices=ProductType.choices)
    company_name = models.CharField(max_length=150, help_text='Manufacturer / brand of the tool or part.')
    product_title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    vehicle_manufacturer = models.CharField(
        max_length=150, blank=True,
        help_text='Spare Parts only — the vehicle maker this part fits (e.g. Maruti, Honda).',
    )
    vehicle_model = models.CharField(
        max_length=150, blank=True,
        help_text='Spare Parts only — the vehicle model this part fits (e.g. Swift, Activa).',
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
    def tracks_stock(self):
        return self.product_type != self.ProductType.SERVICES

    @property
    def is_low_stock(self):
        return self.tracks_stock and self.stock_quantity <= RESTOCK_THRESHOLD


class StockOnboardingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stock_requests_submitted'
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_requests_reviewed',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'Stock request #{self.id} by {self.submitted_by.username} ({self.get_status_display()})'

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING


class StockOnboardingItem(models.Model):
    request = models.ForeignKey(StockOnboardingRequest, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='onboarding_items')
    quantity_to_add = models.PositiveIntegerField()

    def __str__(self):
        return f'+{self.quantity_to_add} x {self.product.product_title}'
