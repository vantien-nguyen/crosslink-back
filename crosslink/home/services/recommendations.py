from typing import List

import numpy as np
from rest_framework.request import Request

from home.dataclasses import (
    CrossSellRecommendation,
    RecommendedCrossSellDiscount,
    RecommendedProduct,
)
from home.helpers.widget_helpers import (
    build_visit_product_url,
    build_visit_shop_url,
    build_widget_url_params,
)
from home.models import CrossSellImpression, Product, Shop, WidgetStatus


class RecommendationService:
    @classmethod
    def get_recommended_shops(cls, purchase_shop: Shop, size: int) -> List[Shop]:
        shops = Shop.objects.exclude(shop_url=purchase_shop.shop_url).all()
        available_shops = [
            shop
            for shop in shops
            if shop.cross_sell_widgets.filter(
                status=WidgetStatus.ACTIVE.value,
            )
        ]
        recommended_shops = np.random.choice(
            available_shops,
            size=min(size, len(available_shops)),
            replace=False,
        )

        return list(recommended_shops)

    @classmethod
    def build_recommendations(
        cls, purchase_shop: Shop, cross_sell_impression: CrossSellImpression, request: Request, size: int
    ) -> List[CrossSellRecommendation]:
        recommendations = []
        widget_url_params = build_widget_url_params(purchase_shop.shop_url, request)
        for cross_sell_widget in cross_sell_impression.cross_sell_widgets.all():
            recommended_shop_url = cross_sell_widget.shop.shop_url
            recommended_products = Product.objects.filter(cms_product_id__in=cross_sell_widget.cms_product_ids).all()
            widget_visit_shop_url = build_visit_shop_url(
                widget_url_params,
                recommended_shop_url,
                request,
                "cross-sell-widgets-rdir",
            )

            widget_products = []
            discount = cross_sell_widget.discount
            for product in recommended_products:
                widget_visit_product_url = build_visit_product_url(
                    widget_url_params, recommended_shop_url, request, "cross-sell-widgets-rdir", product, discount
                )
                product_final_price = discount.apply_discount(product.price) if discount else product.price

                widget_product = RecommendedProduct(
                    product.shortened_title,
                    str(product.price),
                    str(product_final_price),
                    widget_visit_product_url,
                    product.image_url,
                )
                widget_products.append(widget_product)

            cross_sell_discount = (
                RecommendedCrossSellDiscount(
                    discount.code, discount.standard_value(), discount.value_type, discount.status
                )
                if discount
                else None
            )
            recommendations.append(
                CrossSellRecommendation(
                    cross_sell_widget.id,
                    widget_products,
                    str(cross_sell_widget.shop.shop_url),
                    str(cross_sell_widget.shop.name),
                    str(cross_sell_widget.shop.logo_url),
                    cross_sell_discount,
                    widget_visit_shop_url,
                )
            )
        return recommendations
