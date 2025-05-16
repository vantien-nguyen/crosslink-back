import json
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from home.models import CrossSellWidget, WidgetStatus
from home.tests.factories import (
    CrossSellWidgetFactory,
    DiscountFactory,
    ProductFactory,
    ShopFactory,
)
from users.tests.factories import UserFactory


class CrossSellWidgetTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shop = ShopFactory.create()
        cls.user = UserFactory.create(is_active=True, shop=cls.shop)
        cls.discount = DiscountFactory.create(shop=cls.shop)
        cls.products = ProductFactory.create_batch(size=10, shop=cls.shop)
        cls.req_data = {
            **json.load(open("crosslink/home/tests/data/cross_sell.json"))["cross_sell_widget_create_form"],
            **{
                "shop": cls.shop.id,
                "cms_product_ids": [product.cms_product_id for product in cls.shop.products.all()],
                "discount": {
                    **json.load(open("crosslink/home/tests/data/cross_sell.json"))["cross_sell_widget_create_form"][
                        "discount"
                    ],
                    **{"shop": cls.shop.id},
                },
            },
        }

    def test_list_cross_sell_widgets(self):
        self.client.force_authenticate(self.user)
        cross_sell_widgets = CrossSellWidgetFactory.create_batch(size=3, shop=self.shop)
        req_data = {"shop_id": self.shop.id}
        response = self.client.get(reverse("cross-sell-widgets-list"), data=req_data)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "User should be able to list cross_sell widgets",
        )
        self.assertEqual(
            len(response.data),
            len(cross_sell_widgets),
            "User should be able to list cross_sell widgets",
        )

    def test_create_cross_sell_widget(self):
        self.client.force_authenticate(self.user)
        with patch("home.views.cross_sell.create_cms_discount") as mock_create_cms_discount:
            mock_create_cms_discount.return_value = json.load(open("crosslink/home/tests/data/cross_sell.json"))[
                "mock_return_discount_value_success_created"
            ]
            response = self.client.post(
                reverse("cross-sell-widgets-list"),
                data=self.req_data,
                format="json",
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "User should be able to create cross_sell widgets",
            )
            mock_create_cms_discount.assert_called_once()

    def test_update_cross_sell_widget(self):
        self.client.force_authenticate(self.user)
        cross_sell_widget = CrossSellWidgetFactory.create(
            shop=self.shop, status=WidgetStatus.ACTIVE.value, discount=DiscountFactory.create(shop=self.shop)
        )
        with patch("home.views.cross_sell.DiscountService.update_discount") as mock_update_discount:
            mock_update_discount.return_value = Response({"message": "Discount updated"}, status=status.HTTP_200_OK)
            response = self.client.put(
                reverse("cross-sell-widgets-detail", kwargs={"pk": cross_sell_widget.id}),
                data=self.req_data,
                format="json",
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                "User should be able to update the cross_sell widget",
            )
            mock_update_discount.assert_called_once()
            cross_sell_widget.refresh_from_db()
            self.assertEqual(cross_sell_widget.name, self.req_data["name"])

    def test_delete_cross_sell_widget(self):
        self.client.force_authenticate(self.user)
        cross_sell_widget = CrossSellWidgetFactory.create(shop=self.shop)
        with patch("home.views.cross_sell.delete_cms_discount") as mock_delete_cms_discount:
            response = self.client.delete(reverse("cross-sell-widgets-detail", kwargs={"pk": cross_sell_widget.id}))
            self.assertEqual(
                response.status_code,
                status.HTTP_204_NO_CONTENT,
                "User should be able to delete cross_sell widget",
            )
            mock_delete_cms_discount.assert_called_once()
            self.assertEqual(
                CrossSellWidget.objects.count(),
                0,
                "There should be no cross_sell widgets after deleting the last one",
            )

    def test_update_cross_sell_widget_status(self):
        self.client.force_authenticate(self.user)
        cross_sell_widget = CrossSellWidgetFactory.create(shop=self.shop, status=WidgetStatus.INACTIVE.value)
        response = self.client.put(
            reverse("cross-sell-widgets-update_status", kwargs={"pk": cross_sell_widget.id}),
            data={"status": WidgetStatus.ACTIVE.value, "shop": self.shop.id},
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "User should be able to update cross_sell widget",
        )
        cross_sell_widget.refresh_from_db()
        self.assertEqual(
            cross_sell_widget.status,
            WidgetStatus.ACTIVE.value,
            "User should be able to update cross_sell widget",
        )


class FailedCrossSellWidgetTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shop = ShopFactory.create()
        cls.user = UserFactory.create(is_active=True, shop=cls.shop)
        cls.discount = DiscountFactory.create(shop=cls.shop)
        cls.products = ProductFactory.create_batch(size=10, shop=cls.shop)
        cls.req_data = {
            **json.load(open("crosslink/home/tests/data/cross_sell.json"))["cross_sell_widget_create_form"],
            **{
                "shop": cls.shop.id,
                "cms_product_ids": [product.cms_product_id for product in cls.shop.products.all()],
                "discount": {
                    **json.load(open("crosslink/home/tests/data/cross_sell.json"))["cross_sell_widget_create_form"][
                        "discount"
                    ],
                    **{"shop": cls.shop.id},
                },
            },
        }
        cls.other_shop = ShopFactory.create()
        cls.other_user = UserFactory.create(is_active=True, shop=cls.other_shop)

    def test_failed_list_cross_sell_widgets_unauthorized_user(self):
        self.client.force_authenticate(self.other_user)
        cross_sell_widgets = CrossSellWidgetFactory.create_batch(size=3, shop=self.shop, discount=self.discount)
        req_data = {"shop_id": self.shop.id}
        response = self.client.get(reverse("cross-sell-widgets-list"), data=req_data)
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "User should not be able to list of cross_sell widgets which belong to other shops",
        )

    def test_failed_create_cross_sell_widget_unauthorized_user(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(
            reverse("cross-sell-widgets-list"),
            data=self.req_data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "User should not be able to create cross sell widgets",
        )

    def test_failed_create_cross_sell_widget_ununique_disount_code(self):
        self.client.force_authenticate(self.user)
        with patch("home.views.cross_sell.create_cms_discount") as mock_create_cms_discount:
            mock_create_cms_discount.return_value = json.load(open("crosslink/home/tests/data/cross_sell.json"))[
                "mock_return_discount_value_error"
            ]
            response = self.client.post(
                reverse("cross-sell-widgets-list"),
                data=self.req_data,
                format="json",
            )
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST, "User should not be able to create cross sell widget"
            )
            mock_create_cms_discount.assert_called_once()
            self.assertEqual(
                response.data["error"], "Code should be unique.", "User should not be able to create cross sell widget"
            )

    def test_failed_update_cross_sell_widget(self):
        self.client.force_authenticate(self.other_user)
        cross_sell_widget = CrossSellWidgetFactory.create(shop=self.shop, status="active", discount=self.discount)
        response = self.client.put(
            reverse("cross-sell-widgets-detail", kwargs={"pk": cross_sell_widget.id}),
            data=self.req_data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "User should not be able to update cross sell widget",
        )

    def test_failed_delete_cross_sell_widget(self):
        self.client.force_authenticate(self.other_user)
        cross_sell_widget = CrossSellWidgetFactory.create(shop=self.shop, status="active", discount=self.discount)
        response = self.client.delete(
            reverse("cross-sell-widgets-detail", kwargs={"pk": cross_sell_widget.id}),
            data=self.req_data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "User should not be able to delete cross sell widget",
        )

    def test_failed_delete_cross_sell_widget_no_cms_discount(self):
        self.client.force_authenticate(self.user)
        cross_sell_widget = CrossSellWidgetFactory.create(
            shop=self.shop, status=WidgetStatus.ACTIVE.value, discount=self.discount
        )
        with patch("home.views.cross_sell.delete_cms_discount") as delete_cms_discount:
            delete_cms_discount.return_value = {"error": "No id"}
            response = self.client.delete(
                reverse("cross-sell-widgets-detail", kwargs={"pk": cross_sell_widget.id}),
                data=self.req_data,
                format="json",
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                "User should not be able to delete cross sell widget",
            )

    def test_failed_update_cross_sell_widget_status(self):
        self.client.force_authenticate(self.other_user)
        cross_sell_widget = CrossSellWidgetFactory.create(
            shop=self.shop, status=WidgetStatus.INACTIVE.value, discount=self.discount
        )
        response = self.client.put(
            reverse("cross-sell-widgets-update_status", kwargs={"pk": cross_sell_widget.id}),
            data={"status": WidgetStatus.ACTIVE.value, "shop": self.shop.id},
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "User should not be able to update cross sell widget",
        )
