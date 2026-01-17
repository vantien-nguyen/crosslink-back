import json
import logging
import os
import time

import django
from confluent_kafka import Consumer

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configs.settings.local")
django.setup()

from home.models import Product, Shop, Variant
from home.utils import get_object_or_none

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "shopify-products")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "shopify-product-consumer")

logger = logging.getLogger(__name__)


def wait_for_kafka(retries=10, delay=5):
    for attempt in range(1, retries + 1):
        try:
            consumer = Consumer(
                {"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS, "group.id": GROUP_ID, "auto.offset.reset": "earliest"}
            )
            consumer.list_topics(timeout=5)  # test connection
            logger.info("Connected to Kafka!")
            return consumer
        except Exception as e:
            logger.warning(f"Kafka not ready (attempt {attempt}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Kafka not available after several retries")


def process_product_event(event: dict):
    event_type = event["type"]
    data = event["product"]

    shop = get_object_or_none(Shop, id=data["shop_id"])
    if not shop:
        logger.warning(f"Shop {data['shop_id']} not found, skipping")
        return

    if event_type in ["create", "update"]:
        product, _ = Product.objects.get_or_create(shop=shop, cms_product_id=data["id"])
        product.title = data.get("title")
        product.cms_product_handle = data.get("handle")
        product.description = data.get("description")
        product.image_url = data.get("image_url")
        product.image_urls = data.get("image_urls", [])
        product.variant_options = data.get("variant_options", [])
        product.save()

        variant_ids = []
        for v in data.get("variants", []):
            image = [img for img in data.get("images", []) if v["id"] in img.get("variant_ids", [])]

            variant_ids.append(v["id"])
            Variant.objects.update_or_create(
                shop_url=shop.shop_url,
                product=product,
                cms_variant_id=v["id"],
                defaults={
                    "price": v["price"],
                    "image_url": image[0].get("src") if image else None,
                    "title": v.get("title"),
                    "options": [
                        v.get("option1"),
                        v.get("option2"),
                        v.get("option3"),
                    ],
                    "inventory_quantity": v.get("inventory_quantity", 0),
                },
            )

        Variant.objects.filter(product=product).exclude(cms_variant_id__in=variant_ids).delete()
        logger.info(f"Processed product {product.cms_product_id} ({event_type})")

    elif event_type == "delete":
        Product.objects.filter(shop=shop, cms_product_id=data["id"]).delete()
        logger.info(f"Deleted product {data['id']}")


def consume():
    consumer = wait_for_kafka()

    consumer.subscribe([TOPIC])
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error(f"Kafka error: {msg.error()}")
                continue

            try:
                event = json.loads(msg.value().decode("utf-8"))
                process_product_event(event)
                consumer.commit()
            except Exception as e:
                logger.exception(f"Failed to process message: {e}")

    except KeyboardInterrupt:
        logger.info("Consumer stopped")
    finally:
        consumer.close()


if __name__ == "__main__":
    consume()
