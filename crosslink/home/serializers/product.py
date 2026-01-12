from home.models import Product, Variant
from rest_framework import serializers


class ProductSerializer(serializers.ModelSerializer):
    shortened_title = serializers.ReadOnlyField()
    price = serializers.ReadOnlyField()
    inventory_quantity = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = "__all__"


class ProductESSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    cms_product_id = serializers.CharField()
    cms_product_handle = serializers.CharField()
    description = serializers.CharField()
    shop_id = serializers.IntegerField()
    shop_url = serializers.CharField()
    created_at = serializers.DateTimeField()
    price = serializers.CharField()
    inventory_quantity = serializers.IntegerField()
    image_url = serializers.CharField()

    shortened_title = serializers.SerializerMethodField()

    # We pass a product map to avoid multiple DB hits
    def __init__(self, instance=None, product_map=None, **kwargs):
        super().__init__(instance, **kwargs)
        self.product_map = product_map or {}

    def get_shortened_title(self, obj):
        title = obj.get("title", "")
        return title[:40] + "..." if len(title) > 40 else title


class VariantSerializer(serializers.ModelSerializer):
    options = serializers.ListField(child=serializers.CharField())
    product = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Variant
        fields = "__all__"
