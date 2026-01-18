import random

from django.core.management.base import BaseCommand
from faker import Faker
from home.models import Product, Shop, Variant

fake = Faker()


class Command(BaseCommand):
    help = "Generate fake products with variants"

    def add_arguments(self, parser):
        parser.add_argument("--shops", type=int, default=5, help="Number of shops")
        parser.add_argument("--products", type=int, default=10000, help="Products per shop")
        parser.add_argument("--variants", type=int, default=3, help="Variants per product")

    def handle(self, *args, **options):
        num_shops = options["shops"]
        num_products = options["products"]
        num_variants = options["variants"]

        # Ensure shops exist
        shops = list(Shop.objects.all()[:num_shops])
        if len(shops) < num_shops:
            for _ in range(num_shops - len(shops)):
                shops.append(Shop.objects.create(shop_url=fake.domain_name(), name=fake.company()))

        for shop in shops:
            products_to_create = []
            variants_to_create = []

            # Create products
            for _ in range(num_products):
                products_to_create.append(
                    Product(
                        shop=shop,
                        title=fake.sentence(nb_words=5),
                        description=fake.paragraph(),
                        cms_product_id=fake.unique.bothify(text="???-#####"),
                        cms_product_handle=fake.slug(),
                        image_url=fake.image_url(),
                        image_urls=[fake.image_url() for _ in range(random.randint(1, 3))],
                    )
                )
            Product.objects.bulk_create(products_to_create, batch_size=100)

            # Create variants
            for product in Product.objects.filter(shop=shop).order_by("-id")[:num_products]:
                for _ in range(num_variants):
                    variants_to_create.append(
                        Variant(
                            product=product,
                            shop_url=shop.shop_url,
                            title=fake.word(),
                            price=round(random.uniform(5, 500), 2),
                            inventory_quantity=random.randint(0, 100),
                            options=[fake.word(), fake.word()],
                        )
                    )
            Variant.objects.bulk_create(variants_to_create, batch_size=200)

        self.stdout.write(self.style.SUCCESS(f"Generated {num_shops*num_products} products with variants"))
