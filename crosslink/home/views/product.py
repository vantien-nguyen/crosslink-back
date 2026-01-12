import logging

from home.documents.products import ProductDocument
from home.models import Product
from home.serializers import ProductESSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

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
        sort = request.GET.get("sort")

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

        product_ids = [doc["id"] for doc in products]
        db_products = Product.objects.filter(id__in=product_ids).select_related("shop").prefetch_related("variants")
        product_map = {product.id: product for product in db_products}

        for doc in products:
            product = product_map.get(doc["id"])
            if not product:
                doc["price"] = "0.00"
                doc["inventory_quantity"] = 0
                doc["image_url"] = ""
                continue

            first_variant = product.variants.first()
            doc["price"] = str(first_variant.price) if first_variant else "0.00"
            doc["inventory_quantity"] = product.inventory_quantity or 0
            doc["image_url"] = product.image_url or ""

        serializer = ProductESSerializer(products, many=True)
        response_data = {"count": total, "results": serializer.data}

        return Response(response_data, status=status.HTTP_200_OK)
