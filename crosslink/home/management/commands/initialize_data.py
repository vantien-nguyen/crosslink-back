import json
import logging

from django.core.management.base import BaseCommand
from home.models import *

# from home.tasks.product import save_cms_products
from users.models import User

logger = logging.getLogger(__file__)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        data = json.load(open("crosslink/home/management/data/data.json"))
        shops_data = data["shops_data"]

        for shop_data in shops_data:
            shop, _ = Shop.objects.get_or_create(
                shop_url=shop_data["shop_url"],
                defaults={
                    "name": shop_data["name"],
                    "email": shop_data["email"],
                    "access_token": shop_data.get("access_token", ""),
                    "test": shop_data["test"],
                    "logo_uploaded": shop_data["logo_uploaded"],
                    "logo_extension": shop_data["logo_extension"],
                    "cms": shop_data["cms"],
                },
            )
            logger.info("Init shop: ", extra={"shop": shop.shop_url})

            user, _ = User.objects.get_or_create(
                email=shop_data["user"]["email"],
                defaults={
                    "first_name": shop_data["user"]["first_name"],
                    "last_name": shop_data["user"]["last_name"],
                    "is_active": shop_data["user"]["is_active"],
                    "shop": shop,
                },
            )
            user.set_password(shop_data["user"]["password"])
            user.save()
            logger.info("Init user: ", extra={"user": user.email})

            # save_cms_products(shop.id)

        # upsell_widgets_data = data["upsell_widgets"]
        # for widget_data in upsell_widgets_data:
        #     shop = Shop.objects.get(shop_url=widget_data["shop_url"])
        #     upsell_widget = UpsellWidget.objects.create(
        #         shop=shop,
        #         name=widget_data["name"],
        #         offer_name=widget_data["offer_name"],
        #         offer_description=widget_data["offer_name"],
        #         upsell_product_id=widget_data["upsell_product_id"],
        #         trigger_product_ids=widget_data["trigger_product_ids"],
        #         discount_value=widget_data["discount_value"],
        #         discount_type=widget_data["discount_type"],
        #     )
        #     upsell_impressions_data = widget_data["upsell_impressions"]
        #     for impression_data in upsell_impressions_data:
        #         impression, _ = UpsellImpression.objects.get_or_create(
        #             upsell_widget=upsell_widget,
        #             checkout_token=impression_data["checkout_token"],
        #             defaults={
        #                 "order_id": impression_data["order_id"],
        #                 "customer_id": impression_data["customer_id"],
        #                 "customer_email": impression_data["customer_email"],
        #                 "customer_first_name": impression_data["customer_first_name"],
        #                 "customer_last_name": impression_data["customer_last_name"],
        #                 "page_url": impression_data["page_url"],
        #             },
        #         )
        #         UpsellConversion.objects.create(
        #             upsell_impression=impression,
        #             variant=Variant.objects.get(pk=impression_data["upsell_conversion"]["variant_id"]),
        #             quantity=impression_data["upsell_conversion"]["quantity"],
        #         )

        # discounts_data = data["discounts"]
        # for discount_data in discounts_data:
        #     shop = Shop.objects.get(shop_url=discount_data["shop_url"])
        #     Discount.objects.create(
        #         shop=shop,
        #         code=discount_data["code"],
        #         value=discount_data["value"],
        #         value_type=discount_data["value_type"],
        #         status=discount_data["status"],
        #         start_date=discount_data["start_date"],
        #         end_date=discount_data["end_date"],
        #         cms_discount_id=discount_data["cms_discount_id"],
        #     )

        # cross_sell_widgets_data = data["cross_sell_widgets"]
        # for cross_sell_widget_data in cross_sell_widgets_data:
        #     shop = Shop.objects.get(shop_url=cross_sell_widget_data["shop_url"])
        #     cross_sell_widget = CrossSellWidget.objects.create(
        #         shop=shop,
        #         name=cross_sell_widget_data["name"],
        #         status=cross_sell_widget_data["status"],
        #         cms_product_ids=cross_sell_widget_data["cms_product_ids"],
        #     )
