import logging
from typing import Any

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from home.models import Shop, UpsellWidget
from home.permissions import CheckShopPermission
from home.serializers import UpsellWidgetSerializer
from home.utils import get_object_or_none
from home.views.base import BaseModelViewset
from shopify_app.services import ShopifyApiService

logger = logging.getLogger(__file__)


class UpsellWidgetViewSet(BaseModelViewset):
    queryset = UpsellWidget.objects.all().order_by("name")
    serializer_class = UpsellWidgetSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticated, CheckShopPermission(["shop_id", "shop"])]
    authentication_classes = [JWTAuthentication]

    @action(
        detail=False,
        methods=["get"],
        url_name="extension",
        url_path="extension",
    )
    def extension(self, request: Request, *arg: Any, **kwargs: Any) -> Response:
        shop = get_object_or_none(Shop, shop_url=request.GET.get("shop_url"))
        if not shop:
            return Response({"message": "Shop not found"}, status=status.HTTP_404_NOT_FOUND)

        shopify_service = ShopifyApiService(shop)
        app_response = shopify_service.check_post_purchase_app_in_use()

        if app_response["data"]["app"]["isPostPurchaseAppInUse"]:
            return Response({"app_in_use": True, "shop_url": shop.shop_url})

        return Response({"app_in_use": False, "shop_url": shop.shop_url})
