import random
import string
import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand
from faker import Faker
from home.models import Product, Shop, Variant

fake = Faker()


def random_id(prefix: str, length: int = 10) -> str:
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class Command(BaseCommand):
    help = "Generate fake shops, products, and variants for Elasticsearch testing"

    def add_arguments(self, parser):
        parser.add_argument("--shops", type=int, default=50)
        parser.add_argument("--products-per-shop", type=int, default=2000)
        parser.add_argument("--max-variants", type=int, default=4)

    def handle(self, *args, **options):
        shop_count = options["shops"]
        products_per_shop = options["products_per_shop"]
        max_variants = options["max_variants"]

        self.stdout.write("Creating shops...")
        shops = [
            Shop(
                name=fake.company(),
                email=fake.company_email(),
                shop_url=f"{fake.domain_word()}-{uuid.uuid4().hex[:6]}.myshopify.com",
                access_token=random_id("tok_", 20),
                test=True,
            )
            for _ in range(shop_count)
        ]
        Shop.objects.bulk_create(shops)
        shops = list(Shop.objects.all())

        self.stdout.write("Creating products & variants...")
        product_batch = []
        variant_batch = []

        for shop in shops:
            for _ in range(products_per_shop):
                product = Product(
                    shop=shop,
                    title=fake.catch_phrase(),
                    description=fake.text(max_nb_chars=500),
                    image_url=fake.image_url(),
                    image_urls=[fake.image_url() for _ in range(random.randint(1, 4))],
                    cms_product_id=random_id("prod_", 12),
                    cms_product_handle=fake.slug(),
                    variant_options=[
                        {"name": "Size", "values": ["S", "M", "L", "XL"]},
                        {"name": "Color", "values": ["Black", "White", "Blue", "Red"]},
                    ],
                )
                product_batch.append(product)

                if len(product_batch) >= 1000:
                    Product.objects.bulk_create(product_batch)
                    self._create_variants(product_batch, variant_batch, max_variants)
                    product_batch.clear()
                    variant_batch.clear()

        if product_batch:
            Product.objects.bulk_create(product_batch)
            self._create_variants(product_batch, variant_batch, max_variants)

        self.stdout.write(self.style.SUCCESS("Fake catalog generation completed 🚀"))

    def _create_variants(self, products, variant_batch, max_variants):
        products = Product.objects.filter(id__in=[p.id for p in products])

        for product in products:
            for _ in range(random.randint(1, max_variants)):
                variant_batch.append(
                    Variant(
                        product=product,
                        shop_url=product.shop.shop_url,
                        title=f"{product.title} Variant",
                        image_url=product.image_url,
                        price=Decimal(random.uniform(5, 500)).quantize(Decimal("0.01")),
                        options=[
                            random.choice(["S", "M", "L", "XL"]),
                            random.choice(["Black", "White", "Blue", "Red"]),
                        ],
                        inventory_quantity=random.randint(0, 500),
                        cms_variant_id=random_id("var_", 12),
                    )
                )

        Variant.objects.bulk_create(variant_batch)
