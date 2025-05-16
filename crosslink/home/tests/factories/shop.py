import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from home.models import CMS, Shop


class ShopFactory(DjangoModelFactory):
    name = factory.Faker("text", max_nb_chars=64)
    email = factory.Faker("email")
    shop_url = factory.Faker("url")
    access_token = factory.Faker("pystr", max_chars=80)
    test = factory.Faker("boolean")
    logo_uploaded = factory.Faker("boolean")
    logo_extension = factory.Faker("text", max_nb_chars=8)
    cms = FuzzyChoice([value for (value, _) in CMS.choices])

    class Meta:
        model = Shop
        django_get_or_create = ("shop_url",)
