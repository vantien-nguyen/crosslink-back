from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class CrossSellRecommendation:
    """
    Dataclass used for keeping track of cross sell recommendations.
    """

    cross_sell_widget_id: int
    recommended_products: List[RecommendedProduct]
    shop_url: str
    widget_shop_name: str
    shop_logo_url: str
    discount: RecommendedCrossSellDiscount | None
    widget_visit_shop_url: str


@dataclass
class RecommendedProduct:
    title: str
    price: str
    final_price: str
    visit_url: str
    image_url: str


@dataclass
class RecommendedCrossSellDiscount:
    code: str
    value: str
    value_type: str
    status: str
