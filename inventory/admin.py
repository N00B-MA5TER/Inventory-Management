from django.contrib import admin

from inventory.models import Product, ProductType


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_title', 'company_name', 'product_type', 'price', 'stock_quantity', 'is_low_stock')
    list_filter = ('product_type', 'company_name')
    search_fields = ('product_title', 'company_name', 'description')
