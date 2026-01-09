import json
import logging
import uuid
from datetime import datetime

import jwt
from django.apps import apps
from django.shortcuts import get_object_or_404
from home.models import Shop
from home.services.upsell import UpsellService
from home.tasks.upsell import save_upsell_conversion
from home.utils import get_object_or_none
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

logger = logging.getLogger(__file__)


@api_view(("GET",))
def upsell_offer(request: Request) -> Response:
    shop = get_object_or_none(Shop, shop_url=request.GET.get("shop_url"))
    if not shop:
        logger.error("Upsell Offer: Bad Token.")
        return Response({"message:", "Shop not found."}, status=status.HTTP_404_NOT_FOUND)

    token = request.GET.get("token", None)
    if not token:
        logger.error("Upsell Offer: Bad Token.")
        return Response({"message": "Bad Token"}, status=status.HTTP_400_BAD_REQUEST)

    decoded_token = jwt.decode(
        token,
        apps.get_app_config("shopify_app").SHOPIFY_API_SECRET_KEY,
        algorithms=["HS256"],
    )
    upsell_widget = UpsellService.get_upsell_widget(shop, decoded_token["input_data"]["initialPurchase"]["lineItems"])
    if not upsell_widget:
        logger.error("Upsell Offer: No Upsell Widget.")
        return Response(
            {"message": "No Upsell Widget."},
            status=status.HTTP_204_NO_CONTENT,
        )

    upsell_data = UpsellService.get_upsell_offer_data(
        upsell_widget,
        decoded_token["input_data"]["initialPurchase"]["referenceId"],
        decoded_token["input_data"]["initialPurchase"]["customerId"],
    )

    return Response(upsell_data)


@api_view(("POST",))
def sign_changeset(request: Request) -> Response:
    """
    Save information that a product has been purchased thanks to the upsell widget.
    """
    data = json.loads(request.body)
    shop = get_object_or_404(Shop, shop_url=data["shop_url"])

    decoded = jwt.decode(
        data["token"],
        apps.get_app_config("shopify_app").SHOPIFY_API_SECRET_KEY,
        algorithms=["HS256"],
    )
    if decoded["input_data"]["initialPurchase"]["referenceId"] != data["referenceId"]:
        logger.error("Upsell Offer: Apply sign changeset: Bad Token.")
        return Response({"message": "Bad Token."}, status=status.HTTP_400_BAD_REQUEST)

    token = jwt.encode(
        {
            "iss": apps.get_app_config("shopify_app").SHOPIFY_API_KEY,
            "jti": str(uuid.uuid4()),
            "iat": datetime.now(),
            "sub": data["referenceId"],
            "changes": data["changes"],
        },
        apps.get_app_config("shopify_app").SHOPIFY_API_SECRET_KEY,
        algorithm="HS256",
    )

    save_upsell_conversion.delay(
        upsell_widget_id=data["upsell_widget_id"],
        checkout_token=data["referenceId"],
        variant_id=data["changes"][0]["variantId"],
        quantity=data["changes"][0]["quantity"],
    )

    return Response({"token": token})
