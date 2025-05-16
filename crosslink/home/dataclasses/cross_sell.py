from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from home.dataclasses import CrossSellRecommendation
    from home.models import CrossSellImpression, Shop


@dataclass
class CrossSellWidgetContext:
    """
    Dataclass responsible for storing the context of cross_sell widget.
    """

    widget_impression: CrossSellImpression
    shop: Shop
    shipping_first_name: str
    recommendations: List[CrossSellRecommendation]
    widget_callback: str
    environment: str

    @property
    def widget_title(self):
        return self.widget_impression.widget_title()

    @property
    def widget_description(self):
        return self.widget_impression.widget_description()
