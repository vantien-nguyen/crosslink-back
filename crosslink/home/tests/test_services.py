import json
from unittest.mock import patch

from django.urls import reverse
from home.dataclasses import CrossSellRecommendation, RecommendedProduct
from home.services.cross_sell import CrossSellHtmlService
from home.services.discount import DiscountService
from home.tests.factories import CrossSellWidgetFactory, DiscountFactory, ProductFactory, ShopFactory
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase


class CrossSellServicesTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shop = ShopFactory.create()
        cls.other_shop = ShopFactory.create()
        cls.products = ProductFactory.create_batch(size=10, shop=cls.other_shop)
        cls.cross_sell_widget = CrossSellWidgetFactory.create(
            shop=cls.other_shop,
            cms_product_ids=[product.cms_product_id for product in cls.products],
            discount=None,
            status="active",
        )
        cls.request_factory = Request(
            APIRequestFactory().get(
                reverse("shopify:shopify_app_cross_sell_widget"),
                data={
                    "shop": cls.shop.shop_url,
                    "checkout_customer_email": "y893yo812u3218",
                    "checkout_token": "2e21u2093u21",
                    "checkout_order_id": 12321321390,
                    "checkout_customer_id": 2132193823,
                    "checkout_shipping_address_first_name": "John",
                    "checkout_shipping_address_last_name": "FRANCE",
                    "page_url": "https://crosslink.com",
                },
            )
        )

    def test_create_cross_sell_impression(self):
        with patch("home.services.cross_sell.RecommendationService.get_recommended_shops") as mock_recommended_shop:
            mock_recommended_shop.return_value = [self.other_shop]
            impression = CrossSellHtmlService.create_cross_sell_impression(self.shop, self.request_factory, size=2)
            self.assertEqual(impression.purchase_shop_url, self.shop.shop_url)

    def test_widget_context(self):
        with patch("home.services.cross_sell.RecommendationService.build_recommendations") as mock_build_recommendation:
            widget_products = [
                RecommendedProduct(
                    product.shortened_title,
                    str(product.price),
                    str(product.price),
                    "",
                    product.image_url,
                )
                for product in self.products
            ]
            mock_build_recommendation.return_value = [
                CrossSellRecommendation(
                    self.cross_sell_widget.id,
                    widget_products,
                    str(self.cross_sell_widget.shop.shop_url),
                    str(self.cross_sell_widget.shop.name),
                    str(self.cross_sell_widget.shop.logo_url),
                    None,
                    self.other_shop.shop_url,
                )
            ]
            context = CrossSellHtmlService.widget_context(self.request_factory)
            mock_build_recommendation.assert_called_once()
            self.assertNotEqual(context.widget_impression, None)


class DiscountServiceTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shop = ShopFactory.create()
        cls.products = ProductFactory.create_batch(size=10, shop=cls.shop)
        cls.discount = DiscountFactory.create(shop=cls.shop)
        cls.request_data = {
            "shop": cls.shop.id,
            "cms_product_ids": [product.cms_product_id for product in cls.shop.products.all()],
            "name": "Test Widget Edit",
            "discount": {
                "shop": cls.shop.id,
                "id": cls.discount.id,
                "code": "TESTCODE",
                "value": 11.12,
                "value_type": "percentage",
                "status": "active",
                "cms_discount_id": cls.discount.cms_discount_id,
            },
            "status": "active",
        }

    def test_update_discount_successfull_create_cms_discount(self):
        cross_sell_widget = CrossSellWidgetFactory.create(shop=self.shop, discount=None)
        self.request_data["id"] = cross_sell_widget.id
        with patch("home.services.discount.create_cms_discount") as mock_create_cms_discount:
            mock_create_cms_discount.return_value = json.load(open("crosslink/home/tests/data/cross_sell.json"))[
                "mock_return_discount_value_success_created"
            ]
            discount_response = DiscountService.update_discount(cross_sell_widget, self.request_data)
            mock_create_cms_discount.assert_called_once()
            self.assertEqual(discount_response.status_code, status.HTTP_200_OK)

    def test_update_discount_failed_create_cms_discount(self):
        cross_sell_widget = CrossSellWidgetFactory.create(shop=self.shop, discount=None)
        self.request_data["id"] = cross_sell_widget.id
        with patch("home.services.discount.create_cms_discount") as mock_create_cms_discount:
            mock_create_cms_discount.return_value = json.load(open("crosslink/home/tests/data/cross_sell.json"))[
                "mock_return_discount_value_error"
            ]
            discount_response = DiscountService.update_discount(cross_sell_widget, self.request_data)
            mock_create_cms_discount.assert_called_once()
            self.assertEqual(discount_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_discount_successfull_update_cms_discount(self):
        cross_sell_widget = CrossSellWidgetFactory.create(shop=self.shop, discount=self.discount)
        self.request_data["id"] = cross_sell_widget.id
        with patch("home.services.discount.update_cms_discount") as mock_update_cms_discount:
            mock_update_cms_discount.return_value = json.load(open("crosslink/home/tests/data/cross_sell.json"))[
                "mock_return_discount_value_success_updated"
            ]
            discount_response = DiscountService.update_discount(cross_sell_widget, self.request_data)
            mock_update_cms_discount.assert_called_once()
            self.assertEqual(discount_response.status_code, status.HTTP_200_OK)

    def test_update_discount_failed_update_cms_discount(self):
        cross_sell_widget = CrossSellWidgetFactory.create(shop=self.shop, discount=self.discount)
        self.request_data["id"] = cross_sell_widget.id
        with patch("home.services.discount.update_cms_discount") as mock_update_cms_discount:
            mock_update_cms_discount.return_value = json.load(open("crosslink/home/tests/data/cross_sell.json"))[
                "mock_return_discount_value_error"
            ]
            discount_response = DiscountService.update_discount(cross_sell_widget, self.request_data)
            mock_update_cms_discount.assert_called_once()
            self.assertEqual(discount_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_discount_successfull_delete_cms_discount(self):
        cross_sell_widget = CrossSellWidgetFactory.create(
            shop=self.shop, discount=DiscountFactory.create(shop=self.shop)
        )
        request_data = {
            "id": cross_sell_widget.id,
            "shop": self.shop.id,
            "cms_product_ids": [product.cms_product_id for product in self.shop.products.all()],
            "name": "Test Widget Edit",
            "discount": None,
            "status": "active",
        }
        with patch("home.services.discount.delete_cms_discount") as mock_delete_cms_discount:
            discount_response = DiscountService.update_discount(cross_sell_widget, request_data)
            mock_delete_cms_discount.assert_called_once()
            self.assertEqual(discount_response.status_code, status.HTTP_200_OK)

    def test_update_discount_failed_delete_cms_discount(self):
        cross_sell_widget = CrossSellWidgetFactory.create(
            shop=self.shop, discount=DiscountFactory.create(shop=self.shop)
        )
        request_data = {
            "id": cross_sell_widget.id,
            "shop": self.shop.id,
            "cms_product_ids": [product.cms_product_id for product in self.shop.products.all()],
            "name": "Test Widget Edit",
            "discount": None,
            "status": "active",
        }
        with patch("home.services.discount.delete_cms_discount") as mock_delete_cms_discount:
            mock_delete_cms_discount.return_value = {"error": "discount id not exist."}
            discount_response = DiscountService.update_discount(cross_sell_widget, request_data)
            mock_delete_cms_discount.assert_called_once()
            self.assertEqual(discount_response.status_code, status.HTTP_400_BAD_REQUEST)
