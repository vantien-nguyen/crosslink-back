from datetime import datetime, timedelta
from decimal import Decimal

import numpy as np
from django.urls import reverse
from home.tests.factories import (
    CrossSellClickFactory,
    CrossSellConversionFactory,
    CrossSellImpressionFactory,
    CrossSellWidgetFactory,
    DiscountFactory,
    ProductFactory,
    ShopFactory,
    UpsellConversionFactory,
    UpsellImpressionFactory,
    UpsellWidgetFactory,
    VariantFactory,
)
from rest_framework import status
from rest_framework.test import APITestCase
from users.tests.factories import UserFactory


class DashboardTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shop = ShopFactory.create()
        cls.user = UserFactory.create(shop=cls.shop, is_active=True)
        cls.other_shop = ShopFactory.create()
        cls.other_user = UserFactory.create(is_active=True, shop=cls.other_shop)

    def test_list_dashboard(self):
        self.client.force_authenticate(self.user)

        products = ProductFactory.create_batch(size=10, shop=self.shop)
        variants = [VariantFactory.create_batch(size=3, product=product) for product in products]

        upsell_widget = UpsellWidgetFactory.create(shop=self.shop, upsell_product_id=products[0].cms_product_id)
        upsell_impressions = UpsellImpressionFactory.create_batch(size=3, upsell_widget=upsell_widget)
        upsell_conversions = [
            UpsellConversionFactory.create(
                upsell_impression=upsell_impression,
                variant=np.random.choice(products[0].variants.all()),
                quantity=np.random.randint(1, 10),
            )
            for upsell_impression in upsell_impressions
        ]
        cross_sell_widget = CrossSellWidgetFactory.create(
            shop=self.shop,
            cms_product_ids=[p.cms_product_id for p in products[:5]],
            discount=DiscountFactory.create(shop=self.shop),
        )
        cross_sell_impressions = CrossSellImpressionFactory.create_batch(
            size=5,
            purchase_shop_url=self.other_shop.shop_url,
            recommended_shop_urls=[self.shop.shop_url],
            customer_email=self.user.email,
            customer_first_name=self.user.first_name,
            customer_last_name=self.user.last_name,
        )
        cross_sell_clicks = [
            CrossSellClickFactory.create_batch(
                purchase_shop_url=self.shop.shop_url,
                size=np.random.randint(1, 5),
                rdir=f"{self.shop.shop_url}/{np.random.choice(products[:5]).cms_product_handle}/...",
                impression=impression,
            )
            for impression in cross_sell_impressions
        ]
        cross_sell_conversions = [
            CrossSellConversionFactory.create(
                purchase_shop_url=self.shop.shop_url,
                customer_email=self.user.email,
                customer_first_name=self.user.first_name,
                customer_last_name=self.user.last_name,
            )
            for click in cross_sell_clicks
        ]

        yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.today().strftime("%Y-%m-%d")
        tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        req_data = {
            "shop_id": self.shop.id,
            "start_date": yesterday,
            "end_date": tomorrow,
        }
        response = self.client.get(
            reverse("dashboard-list"),
            data=req_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, "User should be able to list dashboard")

        compared_impressions = {"upsell": len(upsell_impressions), "cross_sell": len(cross_sell_impressions)}
        compared_clicks = {"upsell": len(upsell_conversions), "cross_sell": len(cross_sell_clicks)}
        compared_total_sales = {"upsell": len(upsell_conversions), "cross_sell": len(cross_sell_conversions)}
        compared_sales = {
            "upsell": Decimal(sum([upsell_conversion.sales for upsell_conversion in upsell_conversions])),
            "cross_sell": Decimal(
                sum([cross_sell_conversion.sales for cross_sell_conversion in cross_sell_conversions])
            ).quantize(Decimal("0.01")),
        }
        compared_ctr = {
            "upsell": (
                100 * (Decimal(len(upsell_conversions)) / Decimal(len(upsell_impressions)))
                if len(upsell_impressions)
                else Decimal(0)
            ),
            "cross_sell": (
                100 * (Decimal(len(cross_sell_clicks)) / Decimal(len(cross_sell_impressions)))
                if len(cross_sell_impressions)
                else Decimal(0)
            ),
        }
        compared_cr = {
            "upsell": (
                100 * (Decimal(len(upsell_conversions)) / Decimal(len(upsell_conversions)))
                if len(upsell_conversions)
                else Decimal(0)
            ),
            "cross_sell": (
                100 * (Decimal(len(cross_sell_conversions)) / Decimal(len(cross_sell_clicks)))
                if len(cross_sell_clicks)
                else Decimal(0)
            ),
        }

        self.assertEqual(response.data["impressions"], compared_impressions)
        self.assertEqual(response.data["clicks"], compared_clicks)
        self.assertEqual(response.data["total_sales"], compared_total_sales)
        self.assertEqual(response.data["sales"], compared_sales)
        self.assertEqual(response.data["ctr"], compared_ctr)
        self.assertEqual(response.data["cr"], compared_cr)

        compared_daily_impressions = {
            "upsell": {yesterday: 0, today: len(upsell_impressions), tomorrow: 0},
            "cross_sell": {yesterday: 0, today: len(cross_sell_impressions), tomorrow: 0},
        }
        compared_daily_clicks = {
            "upsell": {yesterday: 0, today: len(upsell_conversions), tomorrow: 0},
            "cross_sell": {yesterday: 0, today: len(cross_sell_clicks), tomorrow: 0},
        }
        compared_daily_total_sales = {
            "upsell": {yesterday: 0, today: len(upsell_conversions), tomorrow: 0},
            "cross_sell": {yesterday: 0, today: len(cross_sell_conversions), tomorrow: 0},
        }
        compared_daily_sales = {
            "upsell": {
                yesterday: 0,
                today: Decimal(sum([upsell_conversion.sales for upsell_conversion in upsell_conversions])).quantize(
                    Decimal("0.01")
                ),
                tomorrow: 0,
            },
            "cross_sell": {
                yesterday: 0,
                today: Decimal(
                    sum([cross_sell_conversion.sales for cross_sell_conversion in cross_sell_conversions])
                ).quantize(Decimal("0.01")),
                tomorrow: 0,
            },
        }
        compared_daily_ctrs = {
            "upsell": {
                yesterday: 0,
                today: (
                    100 * (Decimal(len(upsell_conversions)) / Decimal(len(upsell_impressions)))
                    if len(upsell_impressions)
                    else Decimal(0)
                ),
                tomorrow: 0,
            },
            "cross_sell": {
                yesterday: 0,
                today: (
                    100 * (Decimal(len(cross_sell_clicks)) / Decimal(len(cross_sell_impressions)))
                    if len(cross_sell_impressions)
                    else Decimal(0)
                ),
                tomorrow: 0,
            },
        }
        compared_daily_crs = {
            "upsell": {
                yesterday: 0,
                today: (
                    100 * (Decimal(len(upsell_conversions)) / Decimal(len(upsell_conversions)))
                    if len(upsell_conversions)
                    else Decimal(0)
                ),
                tomorrow: 0,
            },
            "cross_sell": {
                yesterday: 0,
                today: (
                    100 * (Decimal(len(cross_sell_conversions)) / Decimal(len(cross_sell_clicks)))
                    if len(cross_sell_clicks)
                    else Decimal(0)
                ),
                tomorrow: 0,
            },
        }

        self.assertEqual(response.data["daily_impressions"], compared_daily_impressions)
        self.assertEqual(response.data["daily_clicks"], compared_daily_clicks)
        self.assertEqual(response.data["daily_total_sales"], compared_daily_total_sales)
        self.assertEqual(response.data["daily_sales"], compared_daily_sales)
        self.assertEqual(response.data["daily_ctrs"], compared_daily_ctrs)
        self.assertEqual(response.data["daily_crs"], compared_daily_crs)

    def test_list_dashboard_unauthorized_user(self):
        self.client.force_authenticate(self.other_user)
        req_data = {
            "shop_id": self.shop.id,
            "start_date": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "end_date": (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
        }
        response = self.client.get(
            reverse("dashboard-list"),
            data=req_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, "User should not be able to list dashboard")
