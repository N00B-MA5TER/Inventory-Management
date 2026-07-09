from django.contrib import admin

from billing.models import Bill, BillItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'created_by', 'total_quantity', 'has_bill', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('customer_name', 'customer_phone')
    inlines = [OrderItemInline]


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 0


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'order', 'total_amount', 'created_at')
    inlines = [BillItemInline]
