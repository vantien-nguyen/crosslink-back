import logging
from typing import Dict
from urllib.parse import urlencode

from django.urls import reverse
from home.models import Discount, Product
from rest_framework.request import Request

logger = logging.getLogger(__file__)


utm_params = urlencode(
    {
        "utm_campaign": "crosslink",
        "utm_medium": "crosslink",
        "utm_source": "crosslink",
    },
    safe="",
)


def build_widget_url_params(purchase_shop_url: str, request: Request) -> dict:
    return {
        "page_url": request.GET.get("page_url", ""),
        "purchase_shop_url": purchase_shop_url,
        "checkout_token": request.GET.get("checkout_token", ""),
    }


def build_visit_shop_url(widget_url_params: Dict, recommended_shop_url: str, request: Request, url: str) -> str:
    widget_visit_shop_url_params = widget_url_params | {"rdir": f"https://{recommended_shop_url}?{utm_params}"}
    return request.build_absolute_uri(reverse(url) + "?" + urlencode(widget_visit_shop_url_params, safe=""))


def build_visit_product_url(
    widget_url_params: Dict,
    recommended_shop_url: str,
    request: Request,
    url: str,
    product: Product,
    discount: Discount | None,
) -> str:
    if discount:
        discount_url_params = urlencode({"redirect": f"/products/{product.cms_product_handle}?{utm_params}"}, safe="")
        rdir = f"https://{recommended_shop_url}/discount/{discount.code}?{discount_url_params}"
    else:
        rdir = f"https://{recommended_shop_url}/products/{product.cms_product_handle}?{utm_params}"

    widget_visit_product_url_params = widget_url_params | {"rdir": rdir}
    return request.build_absolute_uri(reverse(url) + "?" + urlencode(widget_visit_product_url_params, safe=""))
