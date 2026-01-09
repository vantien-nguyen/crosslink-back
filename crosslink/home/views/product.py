import hashlib
import json
import logging
import redis

from django.apps import apps
from home.serializers import ProductESSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from crosslink.home.documents.products import ProductDocument

logger = logging.getLogger(__file__)

redis_client = redis.StrictRedis(
    host=apps.get_app_config("home").REDIS_HOST,
    port=apps.get_app_config("home").REDIS_PORT,
    db=apps.get_app_config("home").REDIS_DB,
    password=apps.get_app_config("home").REDIS_PASSWORD,
    decode_responses=True
)

class ProductViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request: Request, *args, **kwargs):
        query = request.GET.get("search", "")
        limit = int(request.GET.get("limit", 10))
        offset = int(request.GET.get("offset", 0))
        shop_id = request.GET.get("shop_id")
        shop_url = request.GET.get("shop_url")
        sort = request.GET.get("sort")

        cache_key = f"product_es:{hashlib.md5(json.dumps({'q': query, 'limit': limit, 'offset': offset, 'shop_id': shop_id, 'shop_url': shop_url, 'sort': sort}).encode()).hexdigest()}"

        cached = redis_client.get(cache_key)
        if cached:
            return Response(json.loads(cached), status=status.HTTP_200_OK)

        search = ProductDocument.search()

        if query:
            search = search.query("multi_match", query=query, fields=["title", "description"])

        if shop_id:
            search = search.filter("term", shop_id=int(shop_id))
        if shop_url:
            search = search.filter("term", shop_url=shop_url)

        if sort:
            search = search.sort(sort)

        total = search.count()
        results = search[offset : offset + limit].execute()
        products = [hit.to_dict() for hit in results]
        serializer = ProductESSerializer(products, many=True)
        response_data = {
            "count": total,
            "results": serializer.data
        }

        redis_client.set(cache_key, json.dumps(response_data), ex=300)

        return Response(response_data, status=status.HTTP_200_OK)
