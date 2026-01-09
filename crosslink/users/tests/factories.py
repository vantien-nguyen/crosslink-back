import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from home.models import Shop
from users.models import User


class UserFactory(DjangoModelFactory):
    email = factory.Faker("email")
    password = factory.Faker("password")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = factory.Faker("boolean")
    shop = FuzzyChoice(Shop.objects.all())

    class Meta:
        model = User
        django_get_or_create = ("email",)


class AdminUserFactory(UserFactory):
    is_staff = True
