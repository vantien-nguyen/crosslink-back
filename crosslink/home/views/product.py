import logging

from home.models import Product
from home.search.documents import ProductDocument
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
            search = search.query("multi_match", query=query, fields=["title", "description", "variants.title"])

        if shop_id:
            search = search.filter("term", shop_id=int(shop_id))
        if shop_url:
            search = search.filter("term", shop_url=shop_url)

        if sort:
            search = search.sort(sort)

        total = search.count()
        # Execute search with pagination
        results = search[offset : offset + limit].execute()

        # Fetch DB products
        product_ids = [int(hit.meta.id) for hit in results]
        db_products = Product.objects.filter(id__in=product_ids).select_related("shop").prefetch_related("variants")
        product_map = {p.id: p for p in db_products}

        # Build products list with all fields the serializer expects
        products = []
        for hit in results:
            product = product_map.get(int(hit.meta.id))
            doc = hit.to_dict()

            # Ensure all serializer fields exist
            doc_full = {
                "id": int(hit.meta.id),
                "title": doc.get("title", ""),
                "description": doc.get("description", ""),  # <- add default empty string
                "cms_product_id": product.cms_product_id if product else "",
                "cms_product_handle": product.cms_product_handle if product else "",
                "shop_id": product.shop.id if product else None,
                "shop_url": product.shop.shop_url if product else "",
                "created_at": product.created_at if product else None,
                "price": str(product.variants.first().price) if product and product.variants.exists() else "0.00",
                "inventory_quantity": product.inventory_quantity if product else 0,
                "image_url": product.image_url if product else "",
            }
            products.append(doc_full)

        # Serialize
        serializer = ProductESSerializer(products, many=True)
        response_data = {"count": search.count(), "results": serializer.data}

        return Response(response_data, status=status.HTTP_200_OK)
