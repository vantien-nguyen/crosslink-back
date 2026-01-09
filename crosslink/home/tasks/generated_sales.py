import logging
import operator
from functools import reduce
from typing import List

from django.db.models import Q
from home.celery import app
from home.models import CrossSellClick, CrossSellConversion, CrossSellImpression, CrossSellWidget, Product
from home.utils import get_object_or_none

logger = logging.getLogger(__file__)


@app.task
def generated_sales(
    shop_url: str,
    checkout_token: str,
    customer_id: int,
    customer_email: str,
    customer_first_name: str,
    customer_last_name: str,
    cms_variant_ids: List[str],
    cms_product_ids: List[str],
    quantities: List[int],
    total_prices: float,
) -> None:
    if get_object_or_none(CrossSellConversion, purchase_shop_url=shop_url, checkout_token=checkout_token):
        return

    if not total_prices or not cms_variant_ids or not quantities:
        return

    purchased_products = Product.objects.filter(shop__shop_url=shop_url, cms_product_id__in=cms_product_ids).all()

    clicks = CrossSellClick.objects.filter(
        reduce(
            operator.or_,
            [
                Q(rdir__icontains=product_handle)
                for product_handle in list(purchased_products.values_list("cms_product_handle", flat=True))
            ],
        ),
        Q(impression__customer_email=customer_email)
        | Q(impression__customer_first_name=customer_first_name, impression__customer_last_name=customer_last_name),
        impression__recommended_shop_urls__contains=[shop_url],
    ).all()
    impressions = CrossSellImpression.objects.filter(
        Q(customer_email=customer_email)
        | Q(customer_first_name=customer_first_name, customer_last_name=customer_last_name),
        recommended_shop_urls__contains=[shop_url],
    ).all()

    cross_sell_widgets = CrossSellWidget.objects.filter(
        shop__shop_url=shop_url, cross_sell_impressions__in=impressions
    ).all()
    if not cross_sell_widgets:
        return

    purchased_variants = list(zip(cms_variant_ids, cms_product_ids, quantities, total_prices))
    available_product_ids = [id for widget in cross_sell_widgets for id in widget.cms_product_ids]
    selected_variants = [variant for variant in purchased_variants if variant[1] in available_product_ids]
    if not selected_variants:
        return

    cross_sell_conversion_args = {
        "customer_id": customer_id,
        "customer_email": customer_email,
        "customer_first_name": customer_first_name,
        "customer_last_name": customer_last_name,
        "cms_variant_ids": [variant[0] for variant in selected_variants],
        "quantities": [variant[2] for variant in selected_variants],
        "sales": sum([float(variant[3]) for variant in selected_variants]),
    }
    conversion, _ = CrossSellConversion.objects.get_or_create(
        purchase_shop_url=shop_url, checkout_token=checkout_token, defaults=cross_sell_conversion_args
    )
    for click in clicks:
        conversion.clicks.add(click)
    for impression in impressions:
        conversion.impressions.add(impression)
    conversion.save()
