from rest_framework import serializers

from home.models import Product, Variant


class ProductSerializer(serializers.ModelSerializer):
    shortened_title = serializers.ReadOnlyField()
    price = serializers.ReadOnlyField()
    inventory_quantity = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = "__all__"


class VariantSerializer(serializers.ModelSerializer):
    options = serializers.ListField(child=serializers.CharField())
    product = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Variant
        fields = "__all__"
