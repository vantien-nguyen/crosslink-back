from unittest.mock import patch

from django.apps import apps
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APITestCase


class AuthenticationTestCase(APITestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.req_shopify_auth = {
            "shop": "example.myshopify.com",
            "scope": apps.get_app_config("shopify_app").SHOPIFY_API_SCOPES,
            "state": "0.6784241404160823",
            "hmac": "700e2dadb827fcc8609e9d5ce208b2e9cdaab9df07390d2cbca10d7c328fc4bf",
        }
        cls.expected_url = "{}/{}/?shop_url={}".format(
            apps.get_app_config("home").CLIENT_APP_HOST,
            apps.get_app_config("home").CLIENT_SIGNUP_ROUTE,
            "example.myshopify.com",
        )

    def test_shopify_login_successfull(self):
        with patch("shopify_app.views.auth.authenticate") as mock_authentication:
            mock_permission_url = "https://example.myshopify.com/admin/oauth/access_token?client_id=123213&client_secret=973y21b12&code=38129y321b"
            mock_authentication.return_value = Response({"permission_url": mock_permission_url}, status=200)
            response = self.client.get(reverse("shopify:shopify_app_login"), data=self.req_shopify_auth)
            self.assertEqual(
                response.status_code,
                200,
                "User should able to login shopify",
            )
            self.assertEqual(
                response.data["permission_url"],
                mock_permission_url,
                "User should able to login shopify",
            )

    def test_shopify_login_failed(self):
        req_data = self.req_shopify_auth.copy()
        req_data.pop("shop")
        response = self.client.get(reverse("shopify:shopify_app_login"), data=req_data)

        self.assertEqual(
            response.status_code,
            404,
            "User should not able to login shopify",
        )
        self.assertEqual(
            response.data["message"],
            "Shop not found.",
            "User should not able to login shopify",
        )

    def test_shopify_finalize_successfull(self):
        with patch("shopify_app.views.hmac.new") as mock_hmac_new:
            with patch("shopify_app.views.hmac.compare_digest") as mock_hmac_compare:
                with patch("shopify_app.views.auth._new_session") as mock_access_token:
                    with patch("shopify_app.views.auth.create_shop_resources.delay") as mock_create_shop_resource:
                        mock_hmac_compare.return_value = True
                        response = self.client.get(
                            reverse("shopify:shopify_app_finalize"),
                            data=self.req_shopify_auth,
                        )
                        mock_hmac_new.assert_called_once()
                        mock_access_token.assert_called_once()
                        mock_create_shop_resource.assert_called_once()
                        self.assertRedirects(response, self.expected_url, fetch_redirect_response=False)

    def test_shopify_finalize_failed(self):
        with patch("shopify_app.views.hmac.new") as mock_hmac_new:
            with patch("shopify_app.views.hmac.compare_digest") as mock_hmac_compare:
                mock_hmac_compare.return_value = False
                response = self.client.get(reverse("shopify:shopify_app_finalize"), data=self.req_shopify_auth)
                mock_hmac_new.assert_called_once()
                self.assertRedirects(response, "/api/shopify/login/", fetch_redirect_response=False)
