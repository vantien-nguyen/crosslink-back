import logging
from typing import Any

from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from home.models import (
    CrossSellClick,
    CrossSellImpression,
    CrossSellWidget,
    Discount,
    DiscountType,
)
from home.permissions import CheckShopPermission
from home.serializers import CrossSellWidgetSerializer, DiscountSerializer
from home.services.discount import DiscountService
from home.tasks.discount import create_cms_discount, delete_cms_discount
from home.utils import get_object_or_none
from home.views.base import BaseModelViewset

logger = logging.getLogger(__file__)


class CrossSellWidgetViewSet(BaseModelViewset):
    queryset = CrossSellWidget.objects.all().order_by("name")
    serializer_class = CrossSellWidgetSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticated, CheckShopPermission(["shop_id", "shop"])]
    authentication_classes = [JWTAuthentication]

    def create(self, request: Request, *args, **kwargs) -> Response:
        widget_serializer = CrossSellWidgetSerializer(data=request.data)
        widget_serializer.is_valid(raise_exception=True)
        widget_data = widget_serializer.validated_data

        if request.data["discount"]:
            discount_serializer = DiscountSerializer(data=request.data["discount"])
            discount_serializer.is_valid(raise_exception=True)
            discount_data = discount_serializer.validated_data

            cms_discount_result = create_cms_discount(
                discount_data["shop"].id,
                discount_data["code"] if "code" in discount_data else "",
                float(discount_data["value"])
                * (0.01 if discount_data["value_type"] == DiscountType.PERCENTAGE.value else 1),
                discount_data["value_type"],
                widget_data["cms_product_ids"],
            )
            if "error" in cms_discount_result:
                return Response({"error": cms_discount_result["error"]}, status=status.HTTP_400_BAD_REQUEST)

            discount = Discount.objects.create(
                shop=discount_data["shop"],
                code=discount_data["code"],
                value=discount_data["value"],
                value_type=discount_data["value_type"],
                status=cms_discount_result["data"]["discountCodeBasicCreate"]["codeDiscountNode"]["codeDiscount"][
                    "status"
                ].lower(),
                cms_discount_id=cms_discount_result["data"]["discountCodeBasicCreate"]["codeDiscountNode"][
                    "id"
                ].removeprefix("gid://shopify/DiscountCodeNode/"),
            )
        else:
            discount = None

        cross_sell_widget = CrossSellWidget.objects.create(
            shop=widget_data["shop"],
            name=widget_data["name"],
            cms_product_ids=widget_data["cms_product_ids"],
            discount=discount,
        )

        return Response(
            {"message": "Cross sell widget created.", "widget": CrossSellWidgetSerializer(cross_sell_widget).data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        cross_sell_widget = self.get_object()
        response = self.check_shop_id(request, cross_sell_widget.shop.id)
        if response:
            return response

        widget_serializer = CrossSellWidgetSerializer(data=request.data)
        widget_serializer.is_valid(raise_exception=True)
        widget_data = widget_serializer.validated_data

        discount_response = DiscountService.update_discount(cross_sell_widget, request.data)
        if discount_response.status_code != status.HTTP_200_OK:
            return discount_response

        cross_sell_widget.name = widget_data["name"]
        cross_sell_widget.cms_product_ids = widget_data["cms_product_ids"]
        cross_sell_widget.save()

        return Response(
            {"message": "Cross sell widget updated."},
            status=status.HTTP_200_OK,
        )

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        cross_sell_widget = self.get_object()
        response = self.check_shop_id(request, cross_sell_widget.shop.id)
        if response:
            return response

        discount = cross_sell_widget.discount
        if discount:
            cms_discount_result = delete_cms_discount(cross_sell_widget.shop.id, discount.cms_discount_id)
            if "error" in cms_discount_result:
                return Response({"error": cms_discount_result["error"]}, status=status.HTTP_400_BAD_REQUEST)

            discount.delete()

        cross_sell_widget.delete()
        return Response({"message": "Crosssell widget deleted"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["put"], url_path="update-status", url_name="update_status")
    def update_status(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        cross_sell_widget = self.get_object()
        cross_sell_widget.status = request.data.get("status")
        cross_sell_widget.save()
        return Response(
            {
                "message": "Cross sell widget status updated.",
                "widget": CrossSellWidgetSerializer(cross_sell_widget).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_name="rdir",
        url_path="rdir",
        permission_classes=[],
        authentication_classes=[],
    )
    def rdir(self, request: Request) -> HttpResponseRedirect:
        checkout_token = request.GET.get("checkout_token")
        impression = get_object_or_none(CrossSellImpression, checkout_token=checkout_token)

        CrossSellClick.objects.get_or_create(
            purchase_shop_url=request.GET.get("purchase_shop_url"),
            impression=impression,
            rdir=request.GET.get("rdir"),
            defaults={
                "checkout_page_url": request.GET.get("page_url"),
            },
        )

        return HttpResponseRedirect(request.GET.get("rdir"))
