import json
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from home.models import WidgetStatus
from home.serializers import UpsellWidgetSerializer
from home.tests.factories import ProductFactory, ShopFactory, UpsellWidgetFactory
from users.tests.factories import UserFactory


class UpsellWidgetTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shop = ShopFactory.create()
        cls.user = UserFactory.create(is_active=True, shop=cls.shop)
        cls.products = ProductFactory.create_batch(size=10, shop=cls.shop)
        cls.req_data = {
            **json.load(open("crosslink/home/tests/data/upsell.json"))["upsell_create_form"],
            **{
                "shop": cls.shop.id,
                "upsell_product_id": cls.shop.products.all().first().cms_product_id,
                "trigger_product_ids": [product.cms_product_id for product in cls.shop.products.all()],
            },
        }

    def test_successful_list_upsell_widgets(self):
        self.client.force_authenticate(self.user)
        upsell_widgets = UpsellWidgetFactory.create_batch(size=3, shop=self.shop)
        response = self.client.get(reverse("upsell-widgets-list"), data={"shop_id": self.shop.id})
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "User should be able to list of upsell widgets",
        )
        self.assertEqual(
            len(response.data),
            len(upsell_widgets),
            "User should be able to list all upsell widgets from specified shop",
        )

    def test_create_successfull_upsell_widget(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("upsell-widgets-list"),
            data=self.req_data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            "User should be able to create an upsell widget",
        )

    def test_update_successfull_upsell_widget(self):
        self.client.force_authenticate(self.user)
        upsell_widget = UpsellWidgetFactory.create(shop=self.shop, status=WidgetStatus.ACTIVE.value)
        response = self.client.put(
            reverse("upsell-widgets-detail", kwargs={"pk": upsell_widget.id}),
            data=self.req_data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "User should be able to update of upsell widget",
        )
        upsell_widget.refresh_from_db()
        self.assertEqual(UpsellWidgetSerializer(upsell_widget).data, response.data)

    def test_upsell_widget_extension(self):
        self.client.force_authenticate(self.user)
        with patch("home.views.upsell.ShopifyApiService.check_post_purchase_app_in_use") as mock_check_post_purchase:
            mock_check_post_purchase.return_value = {"data": {"app": {"isPostPurchaseAppInUse": True}}}
            response = self.client.get(
                reverse("upsell-widgets-extension"),
                data={"shop_url": self.shop.shop_url},
                format="json",
            )
            mock_check_post_purchase.assert_called_once()
            self.assertEqual(response.data["app_in_use"], True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class FailedUpsellWidgetTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shop = ShopFactory.create()
        cls.user = UserFactory.create(is_active=True, shop=cls.shop)
        cls.other_shop = ShopFactory.create()
        cls.other_user = UserFactory.create(is_active=True, shop=cls.other_shop)
        cls.products = ProductFactory.create_batch(size=10, shop=cls.shop)
        cls.req_data = {
            **json.load(open("crosslink/home/tests/data/upsell.json"))["upsell_create_form"],
            **{
                "shop": cls.shop.id,
                "upsell_product_id": cls.shop.products.all().first().cms_product_id,
                "trigger_product_ids": [product.cms_product_id for product in cls.shop.products.all()],
            },
        }

    def test_failed_list_upsell_widgets_unauthorized_user(self):
        self.client.force_authenticate(self.other_user)
        upsell_widgets = UpsellWidgetFactory.create_batch(size=3, shop=self.shop)
        response = self.client.get(reverse("upsell-widgets-list"), data={"shop_id": self.shop.id})
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "User should not be able to list of upsell widgets which belong to other shops",
        )

    def test_failed_create_upsell_widgets_unauthorized_user(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(
            reverse("upsell-widgets-list"),
            data=self.req_data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "User should not be able to create upsell widgets",
        )

    def test_failed_update_upsell_widget(self):
        self.client.force_authenticate(self.other_user)
        upsell_widget = UpsellWidgetFactory.create(shop=self.shop, status=WidgetStatus.ACTIVE.value)
        response = self.client.put(
            reverse("upsell-widgets-detail", kwargs={"pk": upsell_widget.id}),
            data=self.req_data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "User should not be able to update upsell widgets",
        )

    def test_failed_upsell_widget_extension(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.get(
            reverse("upsell-widgets-extension"),
            data={"shop_url": self.shop.shop_url, "shop": self.shop.id},
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "User should not be able to get of upsell widget extension",
        )

    def test_failed_upsell_widget_extension_no_shop(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(
            reverse("upsell-widgets-extension"),
            data={"shop": self.shop.id},
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "User should not be able to get of upsell widget extension",
        )
