from typing import List

from home.celery import app
from home.models import Shop
from shopify_app.services import ShopifyApiService


@app.task
def create_cms_discount(
    shop_id: int,
    code: str,
    value: float,
    value_type: str,
    cms_product_ids: List[str],
) -> None:
    shop = Shop.objects.get(pk=shop_id)

    # TODO: category cms platform
    shopify_service = ShopifyApiService(shop)
    created_discount_result = shopify_service.create_discount(code, value_type, value, cms_product_ids)

    if "errors" in created_discount_result:
        return {"error": created_discount_result["errors"]}

    if created_discount_result["data"]["discountCodeBasicCreate"]["userErrors"]:
        return {"error": created_discount_result["data"]["discountCodeBasicCreate"]["userErrors"][0]["message"]}

    return {"message": "CMS discount created.", "data": created_discount_result["data"]}


@app.task
def update_cms_discount(
    shop_id: int,
    cms_discount_id: str,
    code: str,
    value: float,
    value_type: str,
    cms_discount_ids_to_add: List[str],
    cms_discount_ids_to_remove: List[str],
) -> None:
    shop = Shop.objects.get(pk=shop_id)

    # TODO: category cms platform
    shopify_service = ShopifyApiService(shop)
    updated_discount_result = shopify_service.update_discount(
        cms_discount_id,
        code,
        value_type,
        value,
        cms_discount_ids_to_add,
        cms_discount_ids_to_remove,
    )

    if "errors" in updated_discount_result:
        return {"error": updated_discount_result["errors"]}

    if updated_discount_result["data"]["discountCodeBasicUpdate"]["userErrors"]:
        return {"error": updated_discount_result["data"]["discountCodeBasicUpdate"]["userErrors"][0]["message"]}

    return {"message": "CMS discount updated.", "data": updated_discount_result["data"]}


@app.task
def delete_cms_discount(
    shop_id: int,
    cms_discount_id: str,
) -> None:
    shop = Shop.objects.get(pk=shop_id)

    # TODO: category cms platform
    shopify_service = ShopifyApiService(shop)
    deleted_discount_result = shopify_service.delete_discount(cms_discount_id)

    if "errors" in deleted_discount_result:
        return {"error": deleted_discount_result["errors"]}

    if deleted_discount_result["data"]["discountCodeDelete"]["userErrors"]:
        return {"error": deleted_discount_result["data"]["discountCodeDelete"]["userErrors"][0]["message"]}

    return {"message": "CMS discount deleted.", "data": deleted_discount_result["data"]}
