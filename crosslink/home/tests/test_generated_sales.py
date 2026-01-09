from home.tasks.generated_sales import generated_sales
from home.tests.factories import (
    CrossSellClickFactory,
    CrossSellConversion,
    CrossSellImpressionFactory,
    CrossSellWidgetFactory,
    DiscountFactory,
    ProductFactory,
    ShopFactory,
    VariantFactory,
)
from rest_framework.test import APITestCase


class GeneratedSalesTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shop = ShopFactory.create()
        cls.products = ProductFactory.create_batch(size=10, shop=cls.shop)
        cls.variants = [VariantFactory.create_batch(size=3, product=product) for product in cls.products]
        cls.discount = DiscountFactory.create(shop=cls.shop)
        cls.cross_sell_widget = CrossSellWidgetFactory.create(
            shop=cls.shop, discount=cls.discount, cms_product_ids=[p.cms_product_id for p in cls.products[1:]]
        )
        cls.impression = CrossSellImpressionFactory.create(recommended_shop_urls=[cls.shop.shop_url])
        cls.impression.cross_sell_widgets.add(cls.cross_sell_widget)
        cls.click = CrossSellClickFactory.create(
            purchase_shop_url=cls.shop.shop_url,
            impression=cls.impression,
            rdir=f"{cls.shop.shop_url}/{cls.products[1].cms_product_handle}/...",
        )

    def test_generated_sales_create_conversion(self):
        purchased_products = self.products[:3]
        purchased_variant_ids = [p.variants.all()[0].cms_variant_id for p in purchased_products]
        generated_sales(
            self.shop.shop_url,
            self.impression.checkout_token,
            self.impression.customer_id,
            self.impression.customer_email,
            self.impression.customer_first_name,
            self.impression.customer_last_name,
            [p.variants.all()[0].cms_variant_id for p in purchased_products],
            [p.cms_product_id for p in purchased_products],
            [1, 2, 3],
            [123, 223, 332],
        )
        conversion = CrossSellConversion.objects.last()
        self.assertEqual(conversion.purchase_shop_url, self.shop.shop_url)
        self.assertEqual(conversion.customer_email, self.impression.customer_email)
        self.assertEqual(conversion.customer_first_name, self.impression.customer_first_name)
        self.assertEqual(conversion.customer_last_name, self.impression.customer_last_name)
        self.assertEqual(conversion.cms_variant_ids, purchased_variant_ids[1:3])
        self.assertEqual(conversion.quantities, [2, 3])
        self.assertEqual(conversion.sales, 555)
        self.assertEqual(conversion.impressions.all()[0], self.impression)
        self.assertEqual(conversion.clicks.all()[0], self.click)

    def test_generated_sales_no_selected_variants(self):
        purchased_products = self.products[:1]
        purchased_variant_ids = [p.variants.all()[0].cms_variant_id for p in purchased_products]
        generated_sales(
            self.shop.shop_url,
            self.impression.checkout_token,
            self.impression.customer_id,
            self.impression.customer_email,
            self.impression.customer_first_name,
            self.impression.customer_last_name,
            [p.variants.all()[0].cms_variant_id for p in purchased_products],
            [p.cms_product_id for p in purchased_products],
            [1],
            [332],
        )
        conversion = CrossSellConversion.objects.last()
        self.assertEqual(conversion, None)
