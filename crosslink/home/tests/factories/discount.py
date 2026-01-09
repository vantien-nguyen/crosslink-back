import datetime

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from home.models import Discount, DiscountStatus, DiscountType, Shop


class DiscountFactory(DjangoModelFactory):
    shop = FuzzyChoice(Shop.objects.all())
    code = factory.Faker("text", max_nb_chars=20)
    value = factory.Faker("pydecimal", left_digits=8, right_digits=2)
    value_type = FuzzyChoice([value_type for (value_type, _) in DiscountType.choices])
    status = FuzzyChoice([status for (status, _) in DiscountStatus.choices])
    start_date = factory.Faker("date_time", tzinfo=datetime.timezone.utc)
    end_date = factory.Faker("date_time", tzinfo=datetime.timezone.utc)
    cms_discount_id = factory.Faker("text", max_nb_chars=20)

    class Meta:
        model = Discount
        django_get_or_create = ("code",)
