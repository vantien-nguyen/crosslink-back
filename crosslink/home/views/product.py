# home/views/product_es.py
import logging

from home.serializers import ProductESSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from crosslink.home.documents.products import ProductDocument

logger = logging.getLogger(__file__)


class ProductViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request: Request, *args, **kwargs):
        query = request.GET.get("search", "")
        limit = int(request.GET.get("limit", 10))
        offset = int(request.GET.get("offset", 0))
        shop_id = request.GET.get("shop_id")
        shop_url = request.GET.get("shop_url")
        sort = request.GET.get("sort")  # e.g., 'price' or '-created_at'

        # Build ES search
        search = ProductDocument.search()

        # Full-text search
        if query:
            search = search.query("multi_match", query=query, fields=["title", "description"])

        # Filter by shop_id or shop_url
        if shop_id:
            search = search.filter("term", shop_id=int(shop_id))
        if shop_url:
            search = search.filter("term", shop_url=shop_url)

        # Sorting
        if sort:
            search = search.sort(sort)

        # Total count
        total = search.count()

        # Pagination
        results = search[offset : offset + limit].execute()

        # Convert ES hits to dict
        products = [hit.to_dict() for hit in results]

        # Serialize
        serializer = ProductESSerializer(products, many=True)

        return Response({"count": total, "results": serializer.data}, status=status.HTTP_200_OK)
