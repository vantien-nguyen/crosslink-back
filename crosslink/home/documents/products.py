from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from home.models import Product


@registry.register_document
class ProductDocument(Document):
    shop_id = fields.IntegerField()
    shop_url = fields.KeywordField()
    title = fields.TextField(
        fields={
            "raw": fields.KeywordField(),
        }
    )
    description = fields.TextField()

    class Index:
        name = "products"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Product
        fields = [
            "id",
            "cms_product_id",
            "cms_product_handle",
            "created_at",
        ]

    def prepare_shop_id(self, instance):
        return instance.shop.id

    def prepare_shop_url(self, instance):
        return instance.shop.shop_url
