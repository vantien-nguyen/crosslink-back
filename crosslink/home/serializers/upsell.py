from home.models import UpsellConversion, UpsellImpression, UpsellWidget
from rest_framework import serializers


class UpsellWidgetSerializer(serializers.ModelSerializer):
    detailed_upsell_product = serializers.ReadOnlyField()
    detailed_trigger_products = serializers.ReadOnlyField()

    class Meta:
        model = UpsellWidget
        fields = "__all__"


class UpsellImpressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpsellImpression
        exclude = ["upsell_widget"]


class UpsellConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpsellConversion
        exclude = ["upsell_impression"]
