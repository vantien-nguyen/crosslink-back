from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase


class ShopifyCrossSellWidgetTestCase(APITestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def test_cross_sell_widget_successful(self):
        with patch("shopify_app.views.cross_sell.CrossSellHtmlService.widget_context") as mock_context:
            with patch("shopify_app.views.cross_sell.generated_sales.delay") as mock_generated_sale:
                response = self.client.get(reverse("shopify:shopify_app_cross_sell_widget"))
                mock_context.assert_called_once()
                mock_generated_sale.assert_called_once()
                self.assertEqual(
                    response.status_code,
                    200,
                )
