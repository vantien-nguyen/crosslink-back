import json
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from home.tests.factories import ProductFactory, ShopFactory


class WebhookTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shop = ShopFactory.create()

    def test_product_create(self):
        req_data = json.load(open("crosslink/shopify_app/tests/data/webhook.json"))["data"]
        with patch("shopify_app.views.webhook.verify_webhook") as mock_verify_webhook:
            with patch("shopify_app.views.webhook.get_object_or_none") as mock_shop:
                mock_verify_webhook.return_value = True
                mock_shop.return_value = self.shop
                response = self.client.post(
                    reverse("shopify:product_create"),
                    data=req_data,
                    format="json",
                )
                mock_verify_webhook.assert_called_once()
                mock_shop.assert_called_once()
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_no_create_draft_product(self):
        req_data = json.load(open("crosslink/shopify_app/tests/data/webhook.json"))["data"]
        req_data["status"] = "draft"
        with patch("shopify_app.views.webhook.verify_webhook") as mock_verify_webhook:
            mock_verify_webhook.return_value = True
            response = self.client.post(
                reverse("shopify:product_create"),
                data=req_data,
                format="json",
            )
            mock_verify_webhook.mock_verify_webhook()
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_product(self):
        req_data = json.load(open("crosslink/shopify_app/tests/data/webhook.json"))["data"]
        product = ProductFactory.create(shop=self.shop, cms_product_id=req_data["id"])
        with patch("shopify_app.views.webhook.verify_webhook") as mock_verify_webhook:
            with patch("shopify_app.views.webhook.get_object_or_none") as mock_shop:
                mock_verify_webhook.return_value = True
                mock_shop.return_value = self.shop
                response = self.client.post(
                    reverse("shopify:product_update"),
                    data=req_data,
                    format="json",
                )
                product.refresh_from_db()
                mock_verify_webhook.mock_verify_webhook()
                mock_shop.mock_verify_webhook()
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(product.title, req_data["title"])

    def test_delete_product(self):
        req_data = json.load(open("crosslink/shopify_app/tests/data/webhook.json"))["data"]
        product = ProductFactory.create(shop=self.shop, cms_product_id=req_data["id"])
        with patch("shopify_app.views.webhook.verify_webhook") as mock_verify_webhook:
            mock_verify_webhook.return_value = True
            response = self.client.post(
                reverse("shopify:product_delete"),
                data=req_data,
                format="json",
            )
            mock_verify_webhook.mock_verify_webhook()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json()["message"], "Product deleted.")
