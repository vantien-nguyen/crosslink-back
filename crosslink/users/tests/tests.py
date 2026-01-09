from django.urls import reverse
from home.tests.factories import ShopFactory
from rest_framework.test import APITestCase
from users.tests.factories import UserFactory


class UserTestCase(APITestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.shop = ShopFactory.create()
        cls.user = UserFactory.create(is_active=True, shop=cls.shop)
        cls.user_data = {
            "email": cls.user.email,
            "password": cls.user.password,
        }
        cls.user.set_password(cls.user.password)
        cls.user.save()

    def test_token_obtain_refresh_and_blacklist(self):
        response = self.client.post(reverse("users:auth_token"), data=self.user_data)
        refresh_token = response.cookies.get("refresh").value
        self.assertEqual(response.status_code, 200, "User should be able to obtain auth token")

        response = self.client.post(reverse("users:auth_token_refresh"))
        self.assertEqual(response.status_code, 200, "User should be able to refresh auth token")

        self.client.cookies["refresh"] = refresh_token
        response = self.client.post(reverse("users:auth_token_blacklist"))
        self.assertEqual(response.status_code, 200, "User should be able to blacklist refresh token")

        response = self.client.post(reverse("users:auth_token_refresh"))
        self.assertEqual(
            response.status_code,
            401,
            "User should not be able to refresh token after blacklisting it",
        )

    def test_signout(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("users:signout"))
        self.assertEqual(response.status_code, 200, "User should be able to signout")
        self.assertEqual(response.data, {"detail": "Successfully logged out."})

        response = self.client.post(reverse("users:auth_token_refresh"))
        self.assertEqual(response.status_code, 401, "User should not be able to refresh auth token")

    def test_signout_failed(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("users:signout"))
        self.client.cookies["refresh"] = ""
        response = self.client.post(reverse("users:signout"))
        self.assertEqual(response.status_code, 400, "User should not be able to signout")

    def test_change_password(self):
        self.client.force_authenticate(self.user)
        req_data = {"current_password": self.user_data["password"], "new_password": "NewPass@123"}
        response = self.client.put(reverse("users:users-change-password"), data=req_data, format="json")
        self.assertEqual(response.status_code, 200, "User should be able to change password")

        response = self.client.post(
            reverse("users:auth_token"), data={"email": self.user_data["email"], "password": req_data["new_password"]}
        )
        self.assertEqual(response.status_code, 200, "User should be able to login using new password")

    def test_change_password_failed(self):
        self.client.force_authenticate(self.user)
        req_data = {"current_password": "badpassword", "new_password": "12u38p19nsd@"}
        response = self.client.put(reverse("users:users-change-password"), data=req_data, format="json")
        self.assertEqual(
            response.status_code,
            400,
            "User shoud not be able to change user password when providing incorrect old password.",
        )
