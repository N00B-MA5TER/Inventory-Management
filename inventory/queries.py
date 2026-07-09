from django.db.models import BooleanField, Case, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from inventory.models import RESTOCK_THRESHOLD, Product


def ranked_products(product_type, search=''):
    """Products for `product_type`, ranked so that low-stock + best-selling-this-month
    items surface first. Low stock is the primary sort key (as a group), monthly sales
    volume breaks ties within and outside that group.
    """
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    qs = Product.objects.filter(product_type=product_type)
    if search:
        qs = qs.filter(Q(product_title__icontains=search) | Q(company_name__icontains=search))

    qs = qs.annotate(
        monthly_sold=Coalesce(
            Sum('order_items__quantity', filter=Q(order_items__order__created_at__gte=month_start)),
            Value(0),
        ),
        low_stock_flag=Case(
            When(stock_quantity__lte=RESTOCK_THRESHOLD, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
    )
    return qs.order_by('-low_stock_flag', '-monthly_sold', 'product_title')


def browsable_products(product_type, search=''):
    """Item listing for browsing/ordering. Only Spare Parts uses the low-stock/best-seller
    ranking for now; Tools and Services stay in simple alphabetical order.
    """
    if product_type == Product.ProductType.SPARE_PARTS:
        return ranked_products(product_type, search=search)

    qs = Product.objects.filter(product_type=product_type)
    if search:
        qs = qs.filter(Q(product_title__icontains=search) | Q(company_name__icontains=search))
    return qs.order_by('product_title')
