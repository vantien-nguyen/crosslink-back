from django.db import models


class ShopifyWebhookEvent(models.Model):
    webhook_id = models.CharField(max_length=255, unique=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.webhook_id
