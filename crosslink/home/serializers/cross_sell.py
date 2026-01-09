from home.models import CrossSellImpression, CrossSellWidget
from home.serializers.discount import DiscountSerializer
from rest_framework import serializers


class CrossSellWidgetSerializer(serializers.ModelSerializer):
    detailed_products = serializers.ReadOnlyField()
    discount = DiscountSerializer(read_only=True)

    class Meta:
        model = CrossSellWidget
        fields = "__all__"


class CrossSellImpressionSerializer(serializers.ModelSerializer):

    class Meta:
        model = CrossSellImpression
        fields = "__all__"
