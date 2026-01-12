from typing import List

from django.contrib.postgres.fields import ArrayField
from django.db import models
from home.models import TimeStampMixin, Widget, WidgetImpression


class CrossSellWidget(Widget):
    shop = models.ForeignKey("Shop", models.CASCADE, related_name="cross_sell_widgets")
    cms_product_ids = ArrayField(base_field=models.CharField(max_length=64))
    discount = models.ForeignKey(
        "Discount",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="cross_sell_widgets",
    )

    class Meta:
        db_table = "cross_sell_widgets"

    @property
    def detailed_products(self) -> List:
        products = (
            self.shop.products.filter(cms_product_id__in=self.cms_product_ids)
            .select_related("shop")
            .prefetch_related("variants")
        )

        from home.serializers.product import ProductSerializer

        return ProductSerializer(products, many=True).data


class CrossSellImpression(WidgetImpression):
    purchase_shop_url = models.URLField()
    recommended_shop_urls = ArrayField(base_field=models.URLField(max_length=1000), default=list, blank=True)
    cross_sell_widgets = models.ManyToManyField(CrossSellWidget, related_name="cross_sell_impressions")

    class Meta:
        db_table = "cross_sell_impressions"
        unique_together = ["purchase_shop_url", "checkout_token"]

    def widget_title(self) -> str:
        return (
            f"{self.customer_first_name}, before leaving us ..."
            if self.customer_first_name
            else "Before leaving us ..."
        )

    def widget_description(self):
        """
        Widget desciption that will be displayed in the cross sell widget plugin.
        """
        return f"We would like you to discover our partners. We were seduced by their products which share our values."


class CrossSellClick(TimeStampMixin):
    purchase_shop_url = models.URLField(null=True)
    rdir = models.URLField(max_length=500, null=True)
    checkout_page_url = models.URLField(max_length=1024, null=True)
    impression = models.ForeignKey(CrossSellImpression, models.CASCADE, related_name="clicks", null=True)

    class Meta:
        db_table = "cross_sell_clicks"
        unique_together = ["purchase_shop_url", "impression", "rdir"]


class CrossSellConversion(TimeStampMixin):
    purchase_shop_url = models.URLField()
    checkout_token = models.CharField(max_length=256, null=True)
    customer_id = models.BigIntegerField(null=True)
    customer_email = models.EmailField(null=True)
    customer_first_name = models.CharField(max_length=128, null=True)
    customer_last_name = models.CharField(max_length=128, null=True)

    cms_variant_ids = ArrayField(base_field=models.CharField(max_length=256), default=list)
    quantities = ArrayField(base_field=models.IntegerField(), default=list)
    sales = models.FloatField()

    clicks = models.ManyToManyField(CrossSellClick, related_name="cross_sell_conversions")
    impressions = models.ManyToManyField(CrossSellImpression, related_name="cross_sell_conversions")

    class Meta:
        db_table = "cross_sell_conversions"
        unique_together = ["purchase_shop_url", "checkout_token"]
