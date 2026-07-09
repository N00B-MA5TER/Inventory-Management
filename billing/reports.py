import calendar
from datetime import datetime, timedelta

from django.db.models import Sum
from django.utils import timezone

from billing.models import OrderItem
from inventory.models import RESTOCK_THRESHOLD, Product

SUMMARY_TYPES = [Product.ProductType.TOOLS, Product.ProductType.SPARE_PARTS]


def _sold_items(product_type, start, end):
    rows = (
        OrderItem.objects.filter(
            product__product_type=product_type,
            order__created_at__gte=start,
            order__created_at__lt=end,
        )
        .values('product__id', 'product__product_title', 'product__company_name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity', 'product__product_title')
    )
    return list(rows)


def _restock_items(product_type):
    return list(
        Product.objects.filter(product_type=product_type, stock_quantity__lte=RESTOCK_THRESHOLD)
        .order_by('stock_quantity', 'product_title')
    )


def _build_sections(start, end):
    sections = []
    for product_type in SUMMARY_TYPES:
        sections.append({
            'label': Product.ProductType(product_type).label,
            'sold_items': _sold_items(product_type, start, end),
            'restock_items': _restock_items(product_type),
        })
    return sections


def daily_summary_context(date):
    start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
    end = start + timedelta(days=1)
    return {
        'period_label': date.strftime('%d %B %Y'),
        'sections': _build_sections(start, end),
        'date': date,
    }


def monthly_summary_context(year, month):
    start = timezone.make_aware(datetime(year, month, 1))
    days_in_month = calendar.monthrange(year, month)[1]
    end = start + timedelta(days=days_in_month)
    return {
        'period_label': start.strftime('%B %Y'),
        'sections': _build_sections(start, end),
        'year': year,
        'month': month,
    }
