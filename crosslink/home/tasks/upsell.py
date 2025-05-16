from home.celery import app
from home.models import UpsellConversion, UpsellImpression, UpsellWidget, Variant
from home.utils import get_object_or_none


@app.task
def save_upsell_conversion(upsell_widget_id: int, checkout_token: str, variant_id: str, quantity: int) -> None:
    upsell_widget = get_object_or_none(UpsellWidget, pk=upsell_widget_id)
    upsell_impression = get_object_or_none(UpsellImpression, upsell_widget=upsell_widget, checkout_token=checkout_token)
    upsell_variant = get_object_or_none(Variant, cms_variant_id=variant_id)
    UpsellConversion.objects.create(upsell_impression=upsell_impression, variant=upsell_variant, quantity=quantity)
