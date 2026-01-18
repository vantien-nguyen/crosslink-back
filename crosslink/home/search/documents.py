from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from home.models import Product


@registry.register_document
class ProductDocument(Document):
    shop_id = fields.IntegerField(attr="shop_id")

    # Use edge_ngram for partial search
    title = fields.TextField(analyzer="edge_ngram_analyzer", search_analyzer="standard")
    description = fields.TextField(analyzer="edge_ngram_analyzer", search_analyzer="standard")

    variants = fields.NestedField(
        properties={
            "title": fields.TextField(analyzer="edge_ngram_analyzer", search_analyzer="standard"),
        }
    )

    class Index:
        name = "products"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {"edge_ngram_analyzer": {"tokenizer": "edge_ngram_tokenizer", "filter": ["lowercase"]}},
                "tokenizer": {
                    "edge_ngram_tokenizer": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 20,
                        "token_chars": ["letter", "digit"],
                    }
                },
            },
        }

    class Django:
        model = Product
        fields = ["cms_product_handle"]
