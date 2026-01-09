import logging
from typing import Any

from django.conf import settings
from django.contrib.auth.hashers import check_password
from home.models import Shop
from home.utils import get_object_or_none
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView
from users.models import User
from users.serializers import (
    CookieTokenRefreshSerializer,
    LoginSerializer,
    SignUpSerializer,
    UserPasswordResetSerializer,
    UserSerializer,
)

logger = logging.getLogger(__file__)


class UserViewset(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=False,
        methods=["post"],
        url_name="signup",
        url_path="signup",
        permission_classes=[AllowAny],
    )
    def signup_user(self, request: Request, *args, **kwargs) -> Response:
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shop = get_object_or_none(Shop, shop_url=serializer.data["shop_url"])
        if not shop:
            return Response(
                {"message": "Shop not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user, _ = User.objects.update_or_create(
            email=serializer.data["email"],
            defaults={
                "first_name": serializer.data["first_name"],
                "last_name": serializer.data["last_name"],
            },
        )
        user.shop = shop
        user.set_password(serializer.data["password"])
        user.is_active = True
        user.save()

        return Response({"message": "User created."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["put"], url_name="change-password", url_path="change-password")
    def change_password(self, request: Request, *arg: Any, **kwargs: Any) -> Response:
        """
        Receives `current_password` and `new_password`.
        Verify that `current_password` is correct and change it to `new_password`.
        """
        user = self.request.user
        serializer = UserPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not check_password(serializer.data["current_password"], user.password):
            logger.info("Change password | Wrong current password", extra={"user": user.email})
            return Response({"message": "Current password doesn't match"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.data["new_password"])
        user.save()

        logger.info("Change password | Password changed successfully", extra={"user": user.email})

        return Response({"message": "Password changed."}, status=status.HTTP_200_OK)


@api_view(("POST",))
def obtain_token_pairs(request: Request) -> Response:
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.data["email"]
    password = serializer.data["password"]
    user = get_object_or_none(User, email=email)

    if not user:
        return Response({"message": "Email not found."}, status=status.HTTP_404_NOT_FOUND)

    if not check_password(password, user.password):
        return Response({"message": "Wrong password."}, status=status.HTTP_404_NOT_FOUND)

    if not user.is_active:
        return Response({"message": "User is not active."}, status=status.HTTP_404_NOT_FOUND)

    refresh = RefreshToken.for_user(user)
    response = Response()
    response.data = {
        "access": str(refresh.access_token),
        "shop_id": user.shop.id if hasattr(user.shop, "id") else None,
        "shop_url": user.shop.shop_url if hasattr(user.shop, "shop_url") else "",
        "shop_name": user.shop.name if hasattr(user.shop, "name") else "",
        "logo_url": user.shop.logo_url if hasattr(user.shop, "logo_url") else "",
    }
    response.set_cookie(
        "refresh",
        str(refresh),
        max_age=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
        httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
        secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
        samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
    )

    return response


class CookieTokenBlacklistView(TokenBlacklistView):
    def post(self, request, *args, **kwargs):
        request.data["refresh"] = request.COOKIES.get("refresh")
        return super().post(request, *args, **kwargs)


class SignOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CookieTokenRefreshView(TokenRefreshView):
    serializer_class = CookieTokenRefreshSerializer

    def finalize_response(self, request: Request, response: Response, *args: Any, **kwargs: Any) -> Response:
        if response.data.get("refresh"):
            response.set_cookie(
                "refresh",
                response.data["refresh"],
                max_age=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
                httponly=True,
            )
            del response.data["refresh"]
        return super().finalize_response(request, response, *args, **kwargs)
