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

    # Computed fields
    shortened_title = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    inventory_quantity = serializers.SerializerMethodField()

    def get_shortened_title(self, obj):
        # obj is a dict from ES
        title = obj.get("title", "")
        return title[:40] + "..." if len(title) > 40 else title

    def get_price(self, obj):
        # If you indexed price in ES, use it. Otherwise default to 0
        return obj.get("price", "0.00")

    def get_inventory_quantity(self, obj):
        return obj.get("inventory_quantity", 0)


class VariantSerializer(serializers.ModelSerializer):
    options = serializers.ListField(child=serializers.CharField())
    product = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Variant
        fields = "__all__"
