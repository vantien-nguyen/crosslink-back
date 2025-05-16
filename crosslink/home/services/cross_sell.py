from typing import Optional

from django.apps import apps
from rest_framework.request import Request

from home.dataclasses.cross_sell import CrossSellWidgetContext
from home.models import CrossSellImpression, CrossSellWidget, Shop, WidgetStatus
from home.services.recommendations import RecommendationService
from home.utils import get_object_or_none


class CrossSellHtmlService:
    @classmethod
    def create_cross_sell_impression(cls, purchase_shop: Shop, request: Request, size: int) -> CrossSellImpression:
        recommended_shops = RecommendationService.get_recommended_shops(purchase_shop, size=size)
        selected_cross_sell_widgets = CrossSellWidget.objects.filter(
            shop__in=recommended_shops, status=WidgetStatus.ACTIVE.value
        ).distinct("shop")
        cross_sell_impression = CrossSellImpression.objects.create(
            purchase_shop_url=purchase_shop.shop_url,
            recommended_shop_urls=[shop.shop_url for shop in recommended_shops],
            customer_email=request.GET.get("checkout_customer_email"),
            checkout_token=request.GET.get("checkout_token"),
            order_id=request.GET.get("checkout_order_id"),
            customer_id=request.GET.get("checkout_customer_id"),
            customer_first_name=request.GET.get("checkout_shipping_address_first_name"),
            customer_last_name=request.GET.get("checkout_shipping_address_last_name"),
            page_url=request.GET.get("page_url"),
        )
        cross_sell_impression.cross_sell_widgets.set(selected_cross_sell_widgets)
        return cross_sell_impression

    @classmethod
    def widget_context(cls, request: Request, size=2) -> Optional[CrossSellWidgetContext]:
        purchase_shop = get_object_or_none(Shop, shop_url=request.GET.get("shop"))
        if not purchase_shop:
            return None

        widget_impression = get_object_or_none(
            CrossSellImpression,
            purchase_shop_url=purchase_shop.shop_url,
            checkout_token=request.GET.get("checkout_token", ""),
        )
        if not widget_impression:
            widget_impression = cls.create_cross_sell_impression(purchase_shop, request, size=size)

        recommendations = RecommendationService.build_recommendations(
            purchase_shop, widget_impression, request, size=size
        )
        if not recommendations:
            return None

        environment = apps.get_app_config("home").ENVIRONMENT
        return CrossSellWidgetContext(
            widget_impression,
            purchase_shop,
            request.GET.get("checkout_shipping_address_first_name"),
            recommendations,
            request.GET.get("jsonp"),
            environment,
        )
