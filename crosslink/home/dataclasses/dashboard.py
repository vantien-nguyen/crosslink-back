from dataclasses import dataclass
from decimal import Decimal
from typing import Dict


@dataclass
class ShopActivity:
    @dataclass
    class SectionCount:
        upsell: int
        cross_sell: int

    @dataclass
    class SectionValue:
        upsell: Decimal
        cross_sell: Decimal

    @dataclass
    class SectionDailyCount:
        upsell: Dict[str, int]
        cross_sell: Dict[str, int]

    @dataclass
    class SectionDailyValue:
        upsell: Dict[str, Decimal]
        cross_sell: Dict[str, Decimal]

    impressions: SectionCount
    clicks: SectionCount
    total_sales: SectionCount
    sales: SectionValue
    ctr: SectionValue
    cr: SectionValue
    daily_impressions: SectionDailyCount
    daily_clicks: SectionDailyCount
    daily_total_sales: SectionDailyCount
    daily_sales: SectionDailyValue
    daily_ctrs: SectionDailyValue
    daily_crs: SectionDailyValue
