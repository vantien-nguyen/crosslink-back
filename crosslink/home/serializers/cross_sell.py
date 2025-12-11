from rest_framework import serializers

from home.models import CrossSellWidget, CrossSellImpression
from home.serializers.discount import DiscountSerializer


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
