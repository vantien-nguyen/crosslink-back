import base64
import hashlib
import hmac
import json
import logging

from django.apps import apps
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from home.models import Product, Shop, Variant
from home.utils import get_object_or_none

logger = logging.getLogger(__file__)


def verify_webhook(data, hmac_header):
    secret_key = apps.get_app_config("shopify_app").SHOPIFY_API_SECRET_KEY
    digest = hmac.new(secret_key.encode("utf-8"), data, digestmod=hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)

    return hmac.compare_digest(computed_hmac, hmac_header.encode("utf-8"))


@api_view(("POST",))
def product_create(request):
    verified = verify_webhook(request.body, request.headers.get("X-Shopify-Hmac-SHA256"))
    if not verified:
        return Response({}, status=status.HTTP_401_UNAUTHORIZED)

    data = json.loads(request.body)
    if data["status"] == "active":
        shop = get_object_or_none(Shop, shop_url=request.headers.get("X-Shopify-Shop-Domain"))
        product = Product.objects.create(
            shop=shop,
            cms_product_id=data["id"],
            title=data["title"],
            image_url=data["image"]["src"],
            image_urls=[img["src"] for img in data["images"]],
            cms_product_handle=data["handle"],
            variant_options=[{"name": option["name"], "values": option["values"]} for option in data["options"]],
            description=data["body_html"],
        )

        for variant in data["variants"]:
            image = [img for img in data["images"] if variant["id"] in img["variant_ids"]]
            Variant.objects.create(
                shop_url=shop.shop_url,
                product=product,
                cms_variant_id=variant["id"],
                image_url=image[0]["src"] if image else None,
                price=variant["price"],
                title=variant["title"],
                options=[
                    variant["option1"],
                    variant["option2"],
                    variant["option3"],
                ],
                inventory_quantity=variant["inventory_quantity"],
            )

        return Response({"message": "Product created"}, status=status.HTTP_201_CREATED)
    return Response({"message": "Ok"}, status=status.HTTP_200_OK)


@api_view(("POST",))
def product_update(request):
    verified = verify_webhook(request.body, request.headers.get("X-Shopify-Hmac-SHA256"))
    if not verified:
        return Response({}, status=status.HTTP_401_UNAUTHORIZED)

    data = json.loads(request.body)
    if data["status"] == "active":
        shop = get_object_or_none(Shop, shop_url=request.headers.get("X-Shopify-Shop-Domain"))
        product, _ = Product.objects.update_or_create(
            shop=shop,
            cms_product_id=data["id"],
            defaults={
                "title": data["title"],
                "description": data["body_html"],
                "cms_product_handle": data["handle"],
                "image_urls": [img["src"] for img in data["images"]],
                "image_url": data["image"]["src"],
                "variant_options": [{"name": option["name"], "values": option["values"]} for option in data["options"]],
            },
        )

        saved_variant_ids = []
        for variant in data["variants"]:
            saved_variant_ids.append(variant["id"])
            image = [img for img in data["images"] if variant["id"] in img["variant_ids"]]
            variant, _ = Variant.objects.update_or_create(
                shop_url=shop.shop_url,
                product=product,
                cms_variant_id=variant["id"],
                defaults={
                    "image_url": image[0]["src"] if image else None,
                    "price": variant["price"],
                    "title": variant["title"],
                    "options": [
                        variant["option1"],
                        variant["option2"],
                        variant["option3"],
                    ],
                    "inventory_quantity": variant["inventory_quantity"],
                },
            )
        Variant.objects.filter(shop_url=shop.shop_url, product=product).exclude(
            cms_variant_id__in=saved_variant_ids
        ).delete()
    else:
        Product.objects.filter(cms_product_id=data["id"]).delete()

    return Response({"message": "Product updated"}, status=status.HTTP_200_OK)


@api_view(("POST",))
def product_delete(request):
    verified = verify_webhook(request.body, request.headers.get("X-Shopify-Hmac-SHA256"))
    if not verified:
        return Response({}, status=status.HTTP_401_UNAUTHORIZED)

    data = json.loads(request.body)
    Product.objects.filter(cms_product_id=data["id"]).delete()

    return Response({"message": "Product deleted."}, status=status.HTTP_200_OK)
