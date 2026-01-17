import base64
import hashlib
import hmac
import json
import logging

from django.apps import apps
from home.kafka.producer import send_product_event
from home.models import Shop
from home.utils import get_object_or_none
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from shopify_app.models import ShopifyWebhookEvent

logger = logging.getLogger(__name__)


def verify_webhook(data, hmac_header):
    secret_key = apps.get_app_config("shopify_app").SHOPIFY_API_SECRET_KEY
    digest = hmac.new(
        secret_key.encode("utf-8"),
        data,
        digestmod=hashlib.sha256,
    ).digest()
    computed_hmac = base64.b64encode(digest)
    return hmac.compare_digest(computed_hmac, hmac_header.encode("utf-8"))


def is_duplicate_webhook(request):
    webhook_id = request.headers.get("X-Shopify-Webhook-Id")
    if webhook_id and ShopifyWebhookEvent.objects.filter(webhook_id=webhook_id).exists():
        return True

    if webhook_id:
        ShopifyWebhookEvent.objects.create(webhook_id=webhook_id)

    return False


@api_view(["POST"])
def product_create(request):
    hmac_header = request.headers.get("X-Shopify-Hmac-SHA256")
    if not hmac_header or not verify_webhook(request.body, hmac_header):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if is_duplicate_webhook(request):
        return Response(status=status.HTTP_200_OK)

    data = json.loads(request.body)

    if data.get("status") != "active":
        return Response(status=status.HTTP_200_OK)

    shop = get_object_or_none(
        Shop,
        shop_url=request.headers.get("X-Shopify-Shop-Domain"),
    )
    if not shop:
        return Response(status=status.HTTP_200_OK)

    send_product_event(
        event_type="create",
        product_data={
            "shop_id": shop.id,
            "id": data["id"],
            "title": data.get("title"),
            "handle": data.get("handle"),
            "description": data.get("body_html"),
            "image_url": (data.get("image") or {}).get("src"),
            "image_urls": [img["src"] for img in data.get("images", [])],
            "variant_options": data.get("options", []),
            "variants": data.get("variants", []),
            "images": data.get("images", []),
        },
    )

    return Response(status=status.HTTP_201_CREATED)


@api_view(["POST"])
def product_update(request):
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not hmac_header or not verify_webhook(request.body, hmac_header):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if is_duplicate_webhook(request):
        return Response(status=status.HTTP_200_OK)

    data = json.loads(request.body)

    shop = get_object_or_none(
        Shop,
        shop_url=request.headers.get("X-Shopify-Shop-Domain"),
    )
    if not shop:
        return Response(status=status.HTTP_200_OK)

    # If product is no longer active → delete
    if data.get("status") != "active":
        send_product_event(
            event_type="delete",
            product_data={
                "shop_id": shop.id,
                "id": data["id"],
            },
        )
        return Response(status=status.HTTP_200_OK)

    send_product_event(
        event_type="update",
        product_data={
            "shop_id": shop.id,
            "id": data["id"],
            "title": data.get("title"),
            "handle": data.get("handle"),
            "description": data.get("body_html"),
            "image_url": (data.get("image") or {}).get("src"),
            "image_urls": [img["src"] for img in data.get("images", [])],
            "variant_options": data.get("options", []),
            "variants": data.get("variants", []),
            "images": data.get("images", []),
        },
    )

    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def product_delete(request):
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not hmac_header or not verify_webhook(request.body, hmac_header):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if is_duplicate_webhook(request):
        return Response(status=status.HTTP_200_OK)

    data = json.loads(request.body)

    shop = get_object_or_none(
        Shop,
        shop_url=request.headers.get("X-Shopify-Shop-Domain"),
    )
    if not shop:
        return Response(status=status.HTTP_200_OK)

    send_product_event(
        event_type="delete",
        product_data={
            "shop_id": shop.id,
            "id": data["id"],
        },
    )

    return Response(status=status.HTTP_200_OK)
