from django.db import models


class TimeStampMixin(models.Model):
    """
    Base class for tracking when objects where created and updated.
    """

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True


class CMS(models.TextChoices):
    SHOPIFY = "Shopfiy"
    PRESTA = "Presta"


class DiscountType(models.TextChoices):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"


class WidgetStatus(models.TextChoices):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class Widget(TimeStampMixin):
    name = models.CharField(max_length=128, blank=True)
    status = models.CharField(choices=WidgetStatus.choices, max_length=12, default=WidgetStatus.ACTIVE.value)

    class Meta:
        abstract = True


class WidgetImpression(TimeStampMixin):
    order_id = models.BigIntegerField(null=True)
    checkout_token = models.CharField(max_length=256, null=True)
    customer_id = models.BigIntegerField(null=True)
    customer_email = models.EmailField(null=True)
    customer_first_name = models.CharField(max_length=128, null=True)
    customer_last_name = models.CharField(max_length=128, null=True)
    page_url = models.URLField(max_length=1024, null=True)

    class Meta:
        abstract = True
