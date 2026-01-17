import json
import logging

from confluent_kafka import Producer
from django.conf import settings

logger = logging.getLogger(__file__)

KAFKA_BOOTSTRAP_SERVERS = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = "shopify-products"

producer_config = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
}

producer = Producer(producer_config)


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed for message {msg.key()}: {err}")
        logger.error(f"Delivery failed for message {msg.key()}: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def send_product_event(event_type: str, product_data: dict):
    """
    event_type: 'create', 'update', 'delete'
    product_data: JSON-serializable dictionary
    """
    message = {
        "type": event_type,
        "product": product_data,
    }
    producer.produce(
        topic=TOPIC,
        key=str(product_data.get("id")),  # optional key for partitioning
        value=json.dumps(message),
        callback=delivery_report,
    )
    producer.flush()
