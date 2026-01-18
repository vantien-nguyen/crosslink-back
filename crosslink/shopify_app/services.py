import json
import logging
from datetime import datetime
from typing import Dict, List, Union

import shopify
from django.apps import apps
from home.models import DiscountType, Shop

logger = logging.getLogger(__name__)


class ShopifyApiService:
    api_version = apps.get_app_config("shopify_app").SHOPIFY_API_VERSION
    api_key = apps.get_app_config("shopify_app").SHOPIFY_API_KEY
    api_secret_key = apps.get_app_config("shopify_app").SHOPIFY_API_SECRET_KEY

    def __init__(self, shop: Shop) -> None:
        self.shop = shop
        self.shopify = shopify

    def _connect_shopify(self):
        shopify.Session.setup(api_key=self.api_key, secret=self.api_secret_key)
        shopify_session = shopify.Session(self.shop.shop_url, self.api_version)
        shopify_session.token = self.shop.access_token
        shopify.ShopifyResource.activate_session(shopify_session)

    def _disconnect_shopify(self):
        shopify.ShopifyResource.clear_session()

    def _create_script_tag(self, src: str):
        query = """
            mutation scriptTagCreate($input: ScriptTagInput!) {
                scriptTagCreate(input: $input) {
                    scriptTag {
                        id
                        src
                    }
                    userErrors {
                        field
                        message
                    }
                }
            }
            """
        return json.loads(
            shopify.GraphQL().execute(
                query=query,
                variables={
                    "input": {
                        "cache": False,
                        "displayScope": "ORDER_STATUS",
                        "src": src,
                    }
                },
            )
        )

    def get_current_shop(self) -> shopify.Shop:
        self._connect_shopify()
        current_shop = self.shopify.Shop.current()
        self._disconnect_shopify()
        return current_shop

    def get_shopify_products(self) -> list:
        self._connect_shopify()
        page_count = 0
        products_count = shopify.Product.count(status="active")
        shopify_products = []
        if products_count > 0:
            page = shopify.Product.find(limit=250, status="active")
            shopify_products.extend(page)
            while page.has_next_page():
                page = page.next_page()
                shopify_products.extend(page)
                page_count += 1

        self._disconnect_shopify()
        return shopify_products

    def create_script_tags(self):
        script_tags_srcs = [
            apps.get_app_config("shopify_app").WIDGET_SCRIPT_TAG_SRC,
            apps.get_app_config("shopify_app").SPLIDE_SCRIPT_TAG_SRC,
        ]

        self._connect_shopify()

        existing_script_tags = shopify.ScriptTag.find()
        if existing_script_tags:
            for script_tag in existing_script_tags:
                shopify.ScriptTag.delete(script_tag.id)

        for src in script_tags_srcs:
            script_tag_response = self._create_script_tag(src)
            if script_tag_response["data"]["scriptTagCreate"]["userErrors"]:
                logger.error(
                    "{}: Error when creating script tag - {}: {}".format(
                        self.shop.shop_url,
                        src,
                        script_tag_response["data"]["scriptTagCreate"]["userErrors"][0]["message"],
                    )
                )

        self._disconnect_shopify()

    def create_discount(
        self,
        code: str,
        value_type: DiscountType,
        amount: float,
        cms_product_ids: List[str],
    ) -> Dict:
        self._connect_shopify()

        amount_dict = (
            {"percentage": amount}
            if value_type == DiscountType.PERCENTAGE.value
            else {"discountAmount": {"amount": amount, "appliesOnEachItem": False}}
        )
        applies_products = {
            "products": {
                "productsToAdd": [f"gid://shopify/Product/{_cms_product_id}" for _cms_product_id in cms_product_ids]
            }
        }

        basicCodeDiscount = {
            "appliesOncePerCustomer": True,
            "code": code,
            "customerGets": {"items": applies_products, "value": amount_dict},
            "customerSelection": {"all": True},
            "endsAt": None,
            "startsAt": datetime.now().isoformat(),
            "title": code,
        }

        query = """
            mutation discountCodeBasicCreate($basicCodeDiscount: DiscountCodeBasicInput!) {
                discountCodeBasicCreate(basicCodeDiscount: $basicCodeDiscount) {
                userErrors { field message code }
                codeDiscountNode {
                    id
                    codeDiscount {
                    ... on DiscountCodeBasic {
                        title
                        summary
                        status
                        codes (first:10) {
                        edges {
                            node {
                            code
                            }
                        }
                        }
                    }
                    }
                }
                }
            }
        """

        result = json.loads(shopify.GraphQL().execute(query=query, variables={"basicCodeDiscount": basicCodeDiscount}))

        self._disconnect_shopify()

        return result

    def update_discount(
        self,
        cms_discount_id: str,
        code: str,
        value_type: DiscountType,
        amount: float,
        cms_product_ids_to_add: List[str],
        cms_product_ids_to_remove: List[str],
    ) -> Dict:
        self._connect_shopify()

        amount_dict = (
            {"percentage": amount}
            if value_type == DiscountType.PERCENTAGE.value
            else {"discountAmount": {"amount": amount, "appliesOnEachItem": False}}
        )
        applies_products = {
            "products": {
                "productsToAdd": [
                    f"gid://shopify/Product/{_cms_product_id}" for _cms_product_id in cms_product_ids_to_add
                ],
                "productsToRemove": [
                    f"gid://shopify/Product/{_cms_product_id}" for _cms_product_id in cms_product_ids_to_remove
                ],
            }
        }

        basicCodeDiscount = {
            "appliesOncePerCustomer": True,
            "code": code,
            "customerGets": {"items": applies_products, "value": amount_dict},
            "customerSelection": {"all": True},
            "endsAt": None,
            "startsAt": datetime.now().isoformat(),
            "title": code,
        }

        query = """
            mutation discountCodeBasicUpdate($basicCodeDiscount: DiscountCodeBasicInput!, $id: ID!) {
                discountCodeBasicUpdate(basicCodeDiscount: $basicCodeDiscount, id: $id) {
                    codeDiscountNode {
                        id
                        codeDiscount {
                            ... on DiscountCodeBasic {
                                title
                                summary
                                status
                                codes (first:10) {
                                    edges {
                                        node {
                                            code
                                        }
                                    }
                                }
                            }
                        }
                    }
                    userErrors {
                        field
                        message
                    }
                }
            }
        """

        result = json.loads(
            shopify.GraphQL().execute(
                query=query,
                variables={
                    "id": f"gid://shopify/DiscountCodeNode/{cms_discount_id}",
                    "basicCodeDiscount": basicCodeDiscount,
                },
            )
        )

        self._disconnect_shopify()

        return result

    def delete_discount(self, cms_discount_id: str) -> Dict:
        self._connect_shopify()

        query = """
            mutation discountCodeDelete($id: ID!) {
                discountCodeDelete(id: $id) {
                    deletedCodeDiscountId
                    userErrors {
                        field
                        message
                    }
                }
            }
        """
        result = json.loads(
            shopify.GraphQL().execute(
                query=query, variables={"id": f"gid://shopify/DiscountCodeNode/{cms_discount_id}"}
            )
        )

        self._disconnect_shopify()
        return result

    def check_post_purchase_app_in_use(self) -> Dict:
        self._connect_shopify()
        query = """
                {
                    app {
                        isPostPurchaseAppInUse
                    }
                }
            """

        result = json.loads(shopify.GraphQL().execute(query=query))
        self._disconnect_shopify()
        return result

    def _get_customer(self, customer_id: Union[int, str, None]) -> shopify.resources.customer.Customer:
        self._connect_shopify()
        if not customer_id:
            customer_data = shopify.customer.Customer
            customer_data.first_name = ""
            customer_data.last_name = ""
            customer_data.email = ""
            return customer_data

        customer = shopify.Customer.find(customer_id)
        self._disconnect_shopify()
        return customer

    def _create_webhook_subscription(self, topic: str, callbackUrl: str):
        query = """
            mutation webhookSubscriptionCreate($topic: WebhookSubscriptionTopic!, $webhookSubscription: WebhookSubscriptionInput!) {
                webhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
                    webhookSubscription {
                        id
                        topic
                        format
                        endpoint {
                            __typename
                            ... on WebhookHttpEndpoint {
                                callbackUrl
                            }
                        }
                    }
                    userErrors {
                        field
                        message
                    }
                }
            }
            """
        return json.loads(
            shopify.GraphQL().execute(
                query=query,
                variables={
                    "topic": topic,
                    "webhookSubscription": {
                        "callbackUrl": callbackUrl,
                        "format": "JSON",
                    },
                },
            )
        )

    def create_webhooks(self) -> None:
        app_host = (
            "https://doctrinal-aliana-uncombated.ngrok-free.dev"
            if apps.get_app_config("home").is_local()
            else apps.get_app_config("home").APP_HOST
        )
        webhooks = [
            {
                "topic": "PRODUCTS_CREATE",
                "callbackUrl": f"{app_host}/api/shopify/webhook/product/create",
            },
            {
                "topic": "PRODUCTS_DELETE",
                "callbackUrl": f"{app_host}/api/shopify/webhook/product/delete",
            },
            {
                "topic": "PRODUCTS_UPDATE",
                "callbackUrl": f"{app_host}/api/shopify/webhook/product/update",
            },
        ]
        self._connect_shopify()

        for webhook in webhooks:
            webhook_response = self._create_webhook_subscription(webhook["topic"], webhook["callbackUrl"])
            if "errors" in webhook_response:
                logger.error(
                    "{}: Error when creating webhook: {}: {}".format(
                        self.shop.shop_url,
                        webhook["topic"],
                        webhook_response["errors"],
                    )
                )
            elif webhook_response["data"]["webhookSubscriptionCreate"]["userErrors"]:
                logger.error(
                    "{}: Error when creating webhook: {}: {}".format(
                        self.shop.shop_url,
                        webhook["topic"],
                        webhook_response["data"]["webhookSubscriptionCreate"]["userErrors"][0]["message"],
                    )
                )
            else:
                logger.info("{}: Create a webhook successfull: {}".format(self.shop.shop_url, webhook["topic"]))

        self._disconnect_shopify()
