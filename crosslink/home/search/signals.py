from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from home.models import Product
from home.search.documents import ProductDocument


@receiver(post_save, sender=Product)
def update_document(sender, instance, **kwargs):
    ProductDocument().update(instance)


@receiver(post_delete, sender=Product)
def delete_document(sender, instance, **kwargs):
    ProductDocument().delete(instance)
