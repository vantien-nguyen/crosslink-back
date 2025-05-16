import json
import random
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from home.tests.factories import (
    ProductFactory,
    ShopFactory,
    UpsellImpressionFactory,
    UpsellWidgetFactory,
    VariantFactory,
)
from users.tests.factories import UserFactory


class ShopifyUpsellTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shop = ShopFactory.create()
        cls.user = UserFactory.create(is_active=True, shop=cls.shop)

    def test_get_upsell_offer(self):
        products = ProductFactory.create_batch(size=5, shop=self.shop)
        prodcut_ids = [p.cms_product_id for p in products]
        for product in products:
            VariantFactory.create_batch(size=3, product=product, shop_url=self.shop.shop_url)
        upsell_widget = UpsellWidgetFactory.create(
            shop=self.shop,
            status="active",
            upsell_product_id=random.choice(products).cms_product_id,
        )
        req_data = {
            "shop_url": self.shop.shop_url,
            "token": "eyehfdoeldi.asdhaodwdew2423.2349u0pda",
            "locale": "en-FR",
        }
        purchased_product = random.choice([p for p in products if p.cms_product_id != upsell_widget.upsell_product_id])
        with patch("jwt.decode") as mock_decoded_token:
            with patch("shopify_app.views.upsell.UpsellService.get_upsell_widget") as mock_get_upsell_widget:
                mock_get_upsell_widget.return_value = upsell_widget
                mocked_token_value = json.load(open("crosslink/shopify_app/tests/data/upsell.json"))["mocked_token"]
                mocked_token_value["input_data"]["initialPurchase"]["lineItems"][0]["product"][
                    "id"
                ] = purchased_product.cms_product_id
                mock_decoded_token.return_value = mocked_token_value

                response = self.client.get(
                    reverse("shopify:shopify_app_upsell_offer"),
                    data=req_data,
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                mock_decoded_token.assert_called_once()

    def test_get_upsell_offer_bad_token(self):
        products = ProductFactory.create_batch(size=5, shop=self.shop)
        prodcut_ids = [p.cms_product_id for p in products]
        for product in products:
            VariantFactory.create_batch(size=3, product=product, shop_url=self.shop.shop_url)
        upsell_widget = UpsellWidgetFactory.create(
            shop=self.shop,
            status="active",
            upsell_product_id=random.choice(prodcut_ids),
        )

        req_data = {"shop_url": self.shop.shop_url, "locale": "en-FR"}
        purchased_product = random.choice([p for p in products if p.cms_product_id != upsell_widget.upsell_product_id])
        mocked_token_value = json.load(open("crosslink/shopify_app/tests/data/upsell.json"))["mocked_token"]
        with patch("jwt.decode") as mock_decoded_token:
            mocked_token_value["input_data"]["initialPurchase"]["lineItems"][0]["product"][
                "id"
            ] = purchased_product.cms_product_id
            mock_decoded_token.return_value = mocked_token_value

            response = self.client.get(
                reverse("shopify:shopify_app_upsell_offer"),
                data=req_data,
                format="json",
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_apply_sign_changeset_offer(self):
        upsell_widget = UpsellWidgetFactory.create(shop=self.shop)
        product = ProductFactory.create(shop=self.shop)
        variant = VariantFactory.create(product=product)
        upsell_impression = UpsellImpressionFactory.create(
            upsell_widget=upsell_widget,
            checkout_token="2y391232813p01",
        )
        req_data = {
            "shop_url": self.shop.shop_url,
            "token": "eyehfdoeldi.asdhaodwdew2423.2349u0pda",
            "referenceId": "2y391232813p01",
            "changes": [
                {
                    "type": "add_variant",
                    "variantId": variant.cms_variant_id,
                    "quantity": 2,
                }
            ],
            "upsell_widget_id": upsell_widget.id,
        }
        with patch("jwt.decode") as mock_decoded_token:
            with patch("jwt.encode") as mock_encode_token:
                with patch("shopify_app.views.upsell.save_upsell_conversion.delay") as mock_save_upsell_conversion:
                    mock_decoded_token.return_value = {
                        "input_data": {"initialPurchase": {"referenceId": "2y391232813p01"}}
                    }
                    mock_encode_token.return_value = "eyehfdoeldi.asdhaodq123wdew2423.2349u0pda"
                    response = self.client.post(
                        reverse("shopify:shopify_app_upsell_sign_changeset"),
                        data=req_data,
                        format="json",
                    )
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    mock_decoded_token.assert_called_once()
                    mock_encode_token.assert_called_once()
                    mock_save_upsell_conversion.assert_called_once()

    def test_apply_sign_changeset_offer_bad_token(self):
        products = ProductFactory.create_batch(size=5, shop=self.shop)
        prodcut_ids = [p.cms_product_id for p in products]
        upsell_widget = UpsellWidgetFactory.create(shop=self.shop)
        product = ProductFactory.create(shop=self.shop)
        variant = VariantFactory.create(product=product)
        upsell_impression = UpsellImpressionFactory.create(
            upsell_widget=upsell_widget,
            checkout_token="2y391232813p01",
        )
        req_data = {
            "shop_url": self.shop.shop_url,
            "token": "eyehfdoeldi.asdhaodwdew2423.2349u0pda",
            "referenceId": "2y391232813p01",
            "changes": [
                {
                    "type": "add_variant",
                    "variantId": variant.cms_variant_id,
                    "quantity": 2,
                }
            ],
            "upsell_widget_id": upsell_widget.id,
        }
        purchased_product = random.choice([p for p in products if p.cms_product_id != upsell_widget.upsell_product_id])
        mocked_token_value = json.load(open("crosslink/shopify_app/tests/data/upsell.json"))["mocked_token"]
        with patch("jwt.decode") as mock_decoded_token:
            mocked_token_value["input_data"]["initialPurchase"]["lineItems"][0]["product"][
                "id"
            ] = purchased_product.cms_product_id
            mock_decoded_token.return_value = mocked_token_value
            response = self.client.post(
                reverse("shopify:shopify_app_upsell_sign_changeset"),
                data=req_data,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
