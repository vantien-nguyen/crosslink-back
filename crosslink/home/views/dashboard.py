from dataclasses import asdict
from datetime import datetime

import pytz
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from home.models import Shop
from home.permissions import CheckShopPermission
from home.serializers import DashboardRequestSerializer
from home.utils import get_object_or_none
from home.views import BaseModelViewset


class DashboardViewSet(BaseModelViewset):
    permission_classes = [IsAuthenticated, CheckShopPermission(["shop_id"])]
    authentication_classes = [JWTAuthentication]

    def list(self, request: Request, *args, **kwargs) -> Response:
        shop_id = request.GET.get("shop_id", None)
        response = self.check_shop_id(request, shop_id)
        if response:
            return response

        serializer = DashboardRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        start_date = datetime.strptime(serializer.data["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(serializer.data["end_date"], "%Y-%m-%d")
        start_date = pytz.utc.localize(start_date)
        end_date = pytz.utc.localize(end_date).replace(hour=23, minute=59)

        shop = get_object_or_none(Shop, pk=shop_id)

        return Response(asdict(shop.activity(start_date, end_date)), status=status.HTTP_200_OK)
