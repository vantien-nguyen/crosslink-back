import logging
from typing import Any

from django.apps import apps
from home.extensions.s3 import s3_client
from home.models import Shop
from home.serializers import ShopSerializer
from home.views.base import BaseModelViewset
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__file__)


class ShopViewSet(BaseModelViewset):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    pagination_class = LimitOffsetPagination

    @action(detail=True, methods=["post"], url_name="add-logo", url_path="add-logo")
    def add_logo(self, request: Request, *arg: Any, **kwargs: Any) -> Response:
        logo_extension = request.data.get("logo_extension", "").split("/")[-1]
        shop = self.get_object()

        if shop.logo_uploaded:
            s3_client.delete_existed_file(filepath=shop.logo_filepath)
        else:
            shop.logo_uploaded = True
        shop.logo_extension = logo_extension
        shop.save()

        upload_data = s3_client.generate_upload_presigned_url(
            filepath=shop.logo_filepath,
            expiry=apps.get_app_config("home").S3_UPLOAD_ATTACHMENT_PRESIGNED_URL_EXPIRY,
        )
        return Response(upload_data, status=status.HTTP_201_CREATED)
