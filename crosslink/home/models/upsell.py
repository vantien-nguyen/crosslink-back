from decimal import Decimal

from django.contrib.postgres.fields import ArrayField
from django.db import models
from home.models import DiscountType, Product, TimeStampMixin, Widget, WidgetImpression


class UpsellWidget(Widget):
    shop = models.ForeignKey("Shop", models.CASCADE, related_name="upsell_widgets")
    offer_name = models.CharField(max_length=256, blank=True)
    offer_description = models.TextField(blank=True)
    upsell_product_id = models.CharField(max_length=64)
    trigger_product_ids = ArrayField(base_field=models.CharField(max_length=64), default=list, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_type = models.CharField(choices=DiscountType.choices, max_length=12, null=True)

    class Meta:
        db_table = "upsell_widgets"

    @property
    def detailed_upsell_product(self) -> dict:
        product = Product.objects.get(shop=self.shop, cms_product_id=self.upsell_product_id)
        return {
            "id": product.id,
            "cms_product_id": product.cms_product_id,
            "title": product.title,
            "shortened_title": product.shortened_title,
            "price": product.price,
            "description": product.description,
            "image_url": product.image_url,
            "image_urls": product.image_urls,
            "inventory_quantity": product.inventory_quantity,
            "variant_options": product.variant_options,
        }

    @property
    def detailed_trigger_products(self) -> dict:
        products = (
            Product.objects.filter(shop=self.shop, cms_product_id__in=self.trigger_product_ids)
            .select_related("shop")
            .prefetch_related("variants")
        )
        from home.serializers import ProductSerializer

        return ProductSerializer(products, many=True).data

    @property
    def detailed_variants(self) -> dict:
        product = Product.objects.get(shop=self.shop, cms_product_id=self.upsell_product_id).select_related("product")
        variants = product.variants.all()
        return [
            {
                "cms_variant_id": variant.cms_variant_id,
                "title": variant.title,
                "price": variant.price,
                "image_url": variant.image_url,
                "options": variant.options,
            }
            for variant in variants
        ]


class UpsellImpression(WidgetImpression):
    upsell_widget = models.ForeignKey("UpsellWidget", models.CASCADE, related_name="upsell_impressions")

    class Meta:
        db_table = "upsell_impressions"
        unique_together = ["upsell_widget", "checkout_token"]


class UpsellConversion(TimeStampMixin):
    upsell_impression = models.OneToOneField(UpsellImpression, models.CASCADE, related_name="upsell_conversion")
    variant = models.ForeignKey("Variant", models.CASCADE, related_name="upsell_conversions")
    quantity = models.IntegerField(default=0)

    class Meta:
        db_table = "upsell_conversions"

    @property
    def sales(self):
        discount_value = self.upsell_impression.upsell_widget.discount_value
        discount_type = self.upsell_impression.upsell_widget.discount_type
        if discount_type == DiscountType.PERCENTAGE:
            discounted_price = self.variant.price * (Decimal(1) - discount_value / Decimal(100))
        else:
            discounted_price = abs(self.variant.price - discount_value)
        return self.quantity * discounted_price
