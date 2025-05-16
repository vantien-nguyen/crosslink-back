import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from home.models import (
    CrossSellClick,
    CrossSellConversion,
    CrossSellImpression,
    CrossSellWidget,
    Discount,
    Shop,
)
from home.tests.factories import WidgetFactory, WidgetImpressionFactory


class CrossSellWidgetFactory(WidgetFactory):
    shop = FuzzyChoice(Shop.objects.all())
    cms_product_ids = factory.Faker("pylist", value_types="str")
    discount = FuzzyChoice(Discount.objects.all())

    class Meta:
        model = CrossSellWidget


class CrossSellImpressionFactory(WidgetImpressionFactory):
    purchase_shop_url = factory.Faker("url")
    recommended_shop_urls = factory.Faker("pylist", value_types="str")

    class Meta:
        model = CrossSellImpression
        django_get_or_create = ("purchase_shop_url", "checkout_token")

    @factory.post_generation
    def cross_sell_widgets(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.cross_sell_widgets.add(*extracted)


class CrossSellClickFactory(DjangoModelFactory):
    purchase_shop_url = factory.Faker("url")
    rdir = factory.Faker("url")
    checkout_page_url = factory.Faker("text")
    impression = FuzzyChoice(CrossSellImpression.objects.all())

    class Meta:
        model = CrossSellClick
        django_get_or_create = ("purchase_shop_url", "impression")


class CrossSellConversionFactory(DjangoModelFactory):
    purchase_shop_url = factory.Faker("url")
    checkout_token = factory.Faker("text", max_nb_chars=256)
    customer_id = factory.Faker("pyint")
    customer_email = factory.Faker("email")
    customer_first_name = factory.Faker("first_name")
    customer_last_name = factory.Faker("last_name")

    cms_variant_ids = factory.Faker("pylist", value_types="str")
    quantities = factory.Faker("pylist", value_types="int")
    sales = factory.Faker("pydecimal", left_digits=8, right_digits=2)

    class Meta:
        model = CrossSellConversion
        django_get_or_create = ("purchase_shop_url", "checkout_token")

    @factory.post_generation
    def clicks(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.clicks.add(*extracted)

    @factory.post_generation
    def impressions(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.impressions.add(*extracted)
