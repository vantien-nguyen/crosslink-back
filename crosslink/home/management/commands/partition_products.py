import logging

from django.core.management.base import BaseCommand
from django.db import connection
from home.models import Shop

logger = logging.getLogger(__file__)

# Prequisite:

# Rename old table
# ALTER TABLE products RENAME TO products_old;


# Create partitioned parent table
# CREATE TABLE products (
#     id BIGSERIAL NOT NULL,
#     shop_id BIGINT NOT NULL,
#     title TEXT,
#     image_url VARCHAR(1000),
#     image_urls TEXT[],
#     cms_product_id VARCHAR(20),
#     cms_product_handle TEXT,
#     variant_options JSONB[],
#     description TEXT,
#     created_at TIMESTAMP DEFAULT now(),
#     updated_at TIMESTAMP DEFAULT now(),
#     PRIMARY KEY (id, shop_id),
#     UNIQUE (shop_id, cms_product_id)
# ) PARTITION BY LIST (shop_id);


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        shop_ids = Shop.objects.values_list("id", flat=True)

        with connection.cursor() as cursor:
            for shop_id in shop_ids:
                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS products_shop_{shop_id} 
                    PARTITION OF products FOR VALUES IN ({shop_id});
                """
                )


# Move existing data into partitions
# INSERT INTO products (
#     id, shop_id, title, image_url, image_urls, cms_product_id,
#     cms_product_handle, variant_options, description, created_at, updated_at
# )
# SELECT
#     id, shop_id, title, image_url, image_urls, cms_product_id,
#     cms_product_handle, variant_options, description, created_at, updated_at
# FROM products_old;


# Add indexes per partition
# with connection.cursor() as cursor:
#     for shop_id in shop_ids:
#         cursor.execute(f"""
#         CREATE INDEX IF NOT EXISTS idx_products_shop_{shop_id}_cms_id
#         ON products_shop_{shop_id} (cms_product_id);
#         """)
#         cursor.execute(f"""
#         CREATE INDEX IF NOT EXISTS idx_products_shop_{shop_id}_title
#         ON products_shop_{shop_id} (title);
#         """)
