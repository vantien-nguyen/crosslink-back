import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from home.models import Product, Shop, Variant


class ProductFactory(DjangoModelFactory):
    shop = FuzzyChoice(Shop.objects.all())
    title = factory.Faker("text")
    image_url = factory.Faker("url")
    image_urls = factory.Faker("pylist", value_types="str")
    cms_product_id = factory.Faker("text", max_nb_chars=20)
    cms_product_handle = factory.Faker("text")
    description = factory.Faker("text")
    variant_options = factory.Faker("pylist", value_types="json")

    class Meta:
        model = Product
        django_get_or_create = ("cms_product_id",)


class VariantFactory(DjangoModelFactory):
    shop_url = factory.Faker("url")
    image_url = factory.Faker("url")
    price = factory.Faker("pydecimal", left_digits=8, right_digits=2, min_value=0)
    title = factory.Faker("text")
    product = FuzzyChoice(Product.objects.all())
    cms_variant_id = factory.Faker("text", max_nb_chars=20)
    options = [factory.Faker("text") for _ in range(3)]
    inventory_quantity = factory.Faker("pyint")

    class Meta:
        model = Variant
        django_get_or_create = ("cms_variant_id",)
