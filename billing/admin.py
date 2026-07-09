from django.contrib import admin

from billing.models import Invoice, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'created_by', 'total_amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('customer_name', 'customer_phone', 'customer_email')
    inlines = [OrderItemInline]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'order', 'created_at')
