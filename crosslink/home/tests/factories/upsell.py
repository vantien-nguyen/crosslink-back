import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from home.models import (
    DiscountType,
    Shop,
    UpsellConversion,
    UpsellImpression,
    UpsellWidget,
)
from home.tests.factories import VariantFactory, WidgetFactory, WidgetImpressionFactory


class UpsellWidgetFactory(WidgetFactory):
    shop = FuzzyChoice(Shop.objects.all())
    offer_name = factory.Faker("text", max_nb_chars=256)
    offer_description = factory.Faker("text")
    upsell_product_id = factory.Faker("text", max_nb_chars=64)
    trigger_product_ids = factory.Faker("pylist", nb_elements=16, variable_nb_elements=True, value_types="str")
    discount_value = factory.Faker("pydecimal", left_digits=8, right_digits=2, min_value=0)
    discount_type = FuzzyChoice([value_type for (value_type, _) in DiscountType.choices])

    class Meta:
        model = UpsellWidget


class UpsellImpressionFactory(WidgetImpressionFactory):
    upsell_widget = FuzzyChoice(UpsellWidget.objects.all())

    class Meta:
        model = UpsellImpression


class UpsellConversionFactory(DjangoModelFactory):
    upsell_impression = factory.SubFactory(UpsellImpressionFactory)
    variant = factory.SubFactory(VariantFactory)
    quantity = factory.Faker("pyint")

    class Meta:
        model = UpsellConversion
