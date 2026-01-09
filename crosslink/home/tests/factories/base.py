import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from home.models import Widget, WidgetImpression, WidgetStatus


class WidgetFactory(DjangoModelFactory):
    name = factory.Faker("text", max_nb_chars=128)
    status = FuzzyChoice([status for (status, _) in WidgetStatus.choices])

    class Meta:
        model = Widget
        abstract = True


class WidgetImpressionFactory(DjangoModelFactory):
    order_id = factory.Faker("pyint")
    checkout_token = factory.Faker("text", max_nb_chars=256)
    customer_id = factory.Faker("pyint")
    customer_email = factory.Faker("email")
    customer_first_name = factory.Faker("first_name")
    customer_last_name = factory.Faker("last_name")
    page_url = factory.Faker("url")

    class Meta:
        model = WidgetImpression
