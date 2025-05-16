from typing import Dict

import numpy as np
from django.db.models import Q

from home.models import Product, Shop, UpsellImpression, UpsellWidget, WidgetStatus
from home.serializers import UpsellWidgetSerializer
from home.utils import get_object_or_none


class UpsellService:
    @classmethod
    def get_upsell_widget(cls, shop: Shop, purchased_products: list) -> UpsellWidget:
        purchased_product_ids = [str(product["product"]["id"]) for product in purchased_products]
        upsell_widgets = shop.upsell_widgets.filter(
            Q(trigger_product_ids__overlap=purchased_product_ids) | Q(trigger_product_ids__len=0),
            status=WidgetStatus.ACTIVE.value,
        ).exclude(upsell_product_id__in=purchased_product_ids)
        available_upsell_widgets = [
            widget for widget in upsell_widgets if widget.detailed_upsell_product["inventory_quantity"] > 0
        ]

        if available_upsell_widgets:
            return np.random.choice(available_upsell_widgets)

        return None

    @classmethod
    def get_upsell_offer_data(cls, upsell_widget: UpsellWidget, checkout_token: str, customer_id: int) -> Dict:
        upsell_data = UpsellWidgetSerializer(upsell_widget).data
        upsell_product = get_object_or_none(Product, cms_product_id=upsell_widget.upsell_product_id)
        upsell_data["variants"] = upsell_product.variants.all().values()

        upsell_impression, _ = UpsellImpression.objects.get_or_create(
            upsell_widget=upsell_widget,
            checkout_token=checkout_token,
            defaults={"customer_id": customer_id},
        )

        return upsell_data
