from django.contrib import admin

from inventory.models import Product, StockOnboardingItem, StockOnboardingRequest


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_title', 'company_name', 'product_type', 'price', 'stock_quantity', 'is_low_stock')
    list_filter = ('product_type', 'company_name')
    search_fields = ('product_title', 'company_name')


class StockOnboardingItemInline(admin.TabularInline):
    model = StockOnboardingItem
    extra = 0


@admin.register(StockOnboardingRequest)
class StockOnboardingRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'submitted_by', 'status', 'submitted_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status',)
    inlines = [StockOnboardingItemInline]
