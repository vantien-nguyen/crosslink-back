from typing import Dict

import numpy as np
from home.models import CrossSellWidget, Discount, DiscountType
from home.serializers import DiscountSerializer
from home.tasks.discount import create_cms_discount, delete_cms_discount, update_cms_discount
from rest_framework import status
from rest_framework.response import Response


class DiscountService:
    @classmethod
    def update_discount(cls, cross_sell_widget: CrossSellWidget, request_data: Dict) -> Response:
        discount = cross_sell_widget.discount
        if not discount and request_data["discount"]:
            discount_serializer = DiscountSerializer(data=request_data["discount"])
            discount_serializer.is_valid(raise_exception=True)
            discount_data = discount_serializer.validated_data
            cms_discount_result = create_cms_discount(
                discount_data["shop"].id,
                discount_data["code"] if "code" in discount_data else "",
                float(discount_data["value"])
                * (0.01 if discount_data["value_type"] == DiscountType.PERCENTAGE.value else 1),
                discount_data["value_type"],
                request_data["cms_product_ids"],
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
            return Response({"message": "Upsell updated"}, status=status.HTTP_200_OK)

        if discount and request_data["discount"]:
            discount_serializer = DiscountSerializer(data=request_data["discount"])
            discount_serializer.is_valid(raise_exception=True)
            discount_data = discount_serializer.validated_data
            cms_discount_result = update_cms_discount(
                discount_data["shop"].id,
                discount.cms_discount_id,
                discount_data["code"] if "code" in discount_data else "",
                float(discount_data["value"])
                * (0.01 if discount_data["value_type"] == DiscountType.PERCENTAGE.value else 1),
                discount_data["value_type"],
                request_data["cms_product_ids"],
                np.setdiff1d(cross_sell_widget.cms_product_ids, request_data["cms_product_ids"]),
            )
            if "error" in cms_discount_result:
                return Response({"error": cms_discount_result["error"]}, status=status.HTTP_400_BAD_REQUEST)

            discount.code = discount_data["code"]
            discount.value = discount_data["value"]
            discount.value_type = discount_data["value_type"]
            discount.status = cms_discount_result["data"]["discountCodeBasicUpdate"]["codeDiscountNode"][
                "codeDiscount"
            ]["status"].lower()
            discount.save()
            return Response({"message": "Upsell updated"}, status=status.HTTP_200_OK)

        if discount and not request_data["discount"]:
            discount = cross_sell_widget.discount
            cms_discount_result = delete_cms_discount(cross_sell_widget.shop.id, discount.cms_discount_id)
            if "error" in cms_discount_result:
                return Response({"error": cms_discount_result["error"]}, status=status.HTTP_400_BAD_REQUEST)

            discount.delete()
            cross_sell_widget.discount = None

        return Response({"message": "Upsell updated"}, status=status.HTTP_200_OK)
