from django.db.models import BooleanField, Case, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from inventory.models import RESTOCK_THRESHOLD, Product


def _apply_filters(qs, search='', company='', vehicle_make='', vehicle_model=''):
    if search:
        qs = qs.filter(Q(product_title__icontains=search) | Q(company_name__icontains=search))
    if company:
        qs = qs.filter(company_name=company)
    if vehicle_make:
        qs = qs.filter(vehicle_manufacturer=vehicle_make)
    if vehicle_model:
        qs = qs.filter(vehicle_model=vehicle_model)
    return qs


def ranked_products(product_type, search='', company='', vehicle_make='', vehicle_model=''):
    """Products for `product_type`, ranked so that low-stock + best-selling-this-month
    items surface first. Low stock is the primary sort key (as a group), monthly sales
    volume breaks ties within and outside that group.
    """
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    qs = Product.objects.filter(product_type=product_type)
    qs = _apply_filters(qs, search=search, company=company, vehicle_make=vehicle_make, vehicle_model=vehicle_model)

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


def browsable_products(product_type, search='', company='', vehicle_make='', vehicle_model=''):
    """Item listing for browsing/ordering. Only Spare Parts uses the low-stock/best-seller
    ranking for now; Tools and Services stay in simple alphabetical order.
    """
    if product_type == Product.ProductType.SPARE_PARTS:
        return ranked_products(
            product_type, search=search, company=company, vehicle_make=vehicle_make, vehicle_model=vehicle_model,
        )

    qs = Product.objects.filter(product_type=product_type)
    qs = _apply_filters(qs, search=search, company=company)
    return qs.order_by('product_title')


def filter_options(product_type, company='', vehicle_make=''):
    """Distinct values available for the filter dropdowns, scoped to `product_type`.
    Vehicle model options narrow to whatever manufacturer is already selected, so the
    two dropdowns behave like a simple cascade without needing any JS.
    """
    qs = Product.objects.filter(product_type=product_type)

    companies = list(
        qs.exclude(company_name='').order_by('company_name')
        .values_list('company_name', flat=True).distinct()
    )

    vehicle_makes = list(
        qs.exclude(vehicle_manufacturer='').order_by('vehicle_manufacturer')
        .values_list('vehicle_manufacturer', flat=True).distinct()
    )

    model_qs = qs.exclude(vehicle_model='')
    if vehicle_make:
        model_qs = model_qs.filter(vehicle_manufacturer=vehicle_make)
    vehicle_models = list(
        model_qs.order_by('vehicle_model').values_list('vehicle_model', flat=True).distinct()
    )

    return {'companies': companies, 'vehicle_makes': vehicle_makes, 'vehicle_models': vehicle_models}
