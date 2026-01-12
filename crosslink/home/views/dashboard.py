import json
from dataclasses import asdict
from datetime import datetime

import pytz
import redis
from django.apps import apps
from home.models import Shop
from home.permissions import CheckShopPermission
from home.serializers import DashboardRequestSerializer
from home.utils import get_object_or_none
from home.views import BaseModelViewset
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

redis_client = redis.StrictRedis(
    host=apps.get_app_config("home").REDIS_HOST,
    port=apps.get_app_config("home").REDIS_PORT,
    db=apps.get_app_config("home").REDIS_DB,
    password=apps.get_app_config("home").REDIS_PASSWORD,
    decode_responses=True,
)
DASHBOARD_CACHE_TTL = 300


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

        cache_key = f"dashboard:{shop_id}:{serializer.data['start_date']}:{serializer.data['end_date']}"
        cached = redis_client.get(cache_key)
        if cached:
            return Response(json.loads(cached), status=status.HTTP_200_OK)

        start_date = datetime.strptime(serializer.data["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(serializer.data["end_date"], "%Y-%m-%d")
        start_date = pytz.utc.localize(start_date)
        end_date = pytz.utc.localize(end_date).replace(hour=23, minute=59)

        shop = get_object_or_none(Shop, pk=shop_id)
        if not shop:
            return Response({"detail": "Shop not found"}, status=status.HTTP_404_NOT_FOUND)

        activity = asdict(shop.activity(start_date, end_date))
        redis_client.set(cache_key, json.dumps(activity, default=str), ex=DASHBOARD_CACHE_TTL)

        return Response(activity, status=status.HTTP_200_OK)
