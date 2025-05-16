import itertools
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

logger = logging.getLogger(__file__)


def get_object_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.MultipleObjectsReturned as _:
        logger.error(f"Multiple objects returned of model {classmodel}")
    except classmodel.DoesNotExist:
        return None


def asdict_with_properties(obj):
    return {
        prop: getattr(obj, prop)
        for prop in dir(obj)
        if not (prop.startswith("__") or callable(getattr(obj, prop, None)))
    }


def group_by_day(l: List, f=lambda x: x.created_at.date()) -> Dict[str, int]:
    """
    Accept a list of objects that have a `created_at` field and a function that specifies how the date can be retrieved.
    By default we use a `created_at` field.
    Return a dictionary (str, int) that groups those object by the same date.
    Each key is the date as string and the value is the number of elements.
    """
    return {str(k): len(list(g)) for k, g in itertools.groupby(l, key=f)}


def sum_by_day(l: List, f=lambda x: x.quantity) -> Dict[str, Decimal]:
    """
    Accept a list of objects that have `created_at` and `quantity` fields.
    Return a dictionary (str, int) that groups those object by the same `created_at` day.
    Each key is the date as string and the value is the sum of quantity fields of grouped objects.
    """
    return {
        str(k): Decimal(sum(list(map(f, list(g))))).quantize(Decimal("0.01"))
        for k, g in itertools.groupby(l, key=lambda x: x.created_at.date())
    }


def daterange(start_date: datetime, end_date: datetime):
    """
    Generates all dates between `start_date` and `end_date` with an increment of 1 day.
    """
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)
