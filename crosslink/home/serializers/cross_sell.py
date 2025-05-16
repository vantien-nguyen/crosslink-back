from rest_framework import serializers

from home.models import CrossSellWidget
from home.serializers.discount import DiscountSerializer


class CrossSellWidgetSerializer(serializers.ModelSerializer):
    detailed_products = serializers.ReadOnlyField()
    discount = DiscountSerializer(read_only=True)

    class Meta:
        model = CrossSellWidget
        fields = "__all__"
