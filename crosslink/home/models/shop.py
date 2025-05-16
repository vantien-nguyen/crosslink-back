from datetime import datetime
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Dict, Tuple

from django.apps import apps
from django.db import models

from home.dataclasses.dashboard import ShopActivity
from home.models import (
    CMS,
    CrossSellClick,
    CrossSellConversion,
    CrossSellImpression,
    TimeStampMixin,
)
from home.models.upsell import UpsellConversion, UpsellImpression
from home.utils import daterange, group_by_day, sum_by_day

CreatedAtDateRange = Dict[str, Tuple[datetime, datetime]]
DailyActivity = Tuple[
    Tuple[ShopActivity.SectionDailyCount, ShopActivity.SectionDailyCount, ShopActivity.SectionDailyCount],
    Tuple[ShopActivity.SectionDailyValue, ShopActivity.SectionDailyValue, ShopActivity.SectionDailyValue],
]


class Shop(TimeStampMixin):
    name = models.CharField(max_length=128)
    email = models.EmailField(null=True)
    shop_url = models.URLField(unique=True)
    access_token = models.CharField(max_length=80)
    test = models.BooleanField(default=False)
    logo_uploaded = models.BooleanField(default=False)
    logo_extension = models.CharField(max_length=8, null=True)
    cms = models.CharField(choices=CMS.choices, max_length=16, default=CMS.SHOPIFY.value)

    class Meta:
        db_table = "shops"

    def __str__(self) -> str:
        return "{}: {}".format(self.name, str(self.shop_url))

    @property
    def logo_url(self) -> str:
        if self.logo_uploaded:
            return "https://{}.s3.{}.amazonaws.com/logos/[{}]{}_logo.{}".format(
                apps.get_app_config("home").S3_BUCKET_NAME,
                apps.get_app_config("home").AWS_REGION,
                self.id,
                self.shop_url,
                self.logo_extension if self.logo_extension else "png",
            )

        return "{}/logos/{}.svg".format(
            apps.get_app_config("home").CLIENT_APP_HOST,
            self.name[0].lower().replace("é", "e"),
        )

    @property
    def logo_filepath(self) -> PurePosixPath:
        return PurePosixPath(
            "logos/[{id}]{url}_logo.{extension}".format(
                id=self.id,
                url=self.shop_url,
                extension=self.logo_extension if self.logo_extension else "png",
            )
        )

    def impressions(self, created_at_date_range: CreatedAtDateRange) -> ShopActivity.SectionCount:
        upsell_impressions_count = UpsellImpression.objects.filter(
            upsell_widget__shop__id=self.id, **created_at_date_range
        ).count()
        cross_sell_impressions_count = CrossSellImpression.objects.filter(
            recommended_shop_urls__contains=[self.shop_url], **created_at_date_range
        ).count()

        return ShopActivity.SectionCount(upsell_impressions_count, cross_sell_impressions_count)

    def clicks(self, created_at_date_range: CreatedAtDateRange) -> ShopActivity.SectionCount:
        upsell_clicks_count = UpsellConversion.objects.filter(
            upsell_impression__upsell_widget__shop__id=self.id, **created_at_date_range
        ).count()
        cross_sell_clicks_count = CrossSellClick.objects.filter(
            rdir__icontains=self.shop_url, **created_at_date_range
        ).count()

        return ShopActivity.SectionCount(upsell_clicks_count, cross_sell_clicks_count)

    def ctr(
        self, clicks: ShopActivity.SectionCount, impressions: ShopActivity.SectionCount
    ) -> ShopActivity.SectionValue:
        upsell_ctr = 100 * (Decimal(clicks.upsell) / Decimal(impressions.upsell)) if impressions.upsell else Decimal(0)
        cross_sell_ctr = (
            100 * (Decimal(clicks.cross_sell) / Decimal(impressions.cross_sell))
            if impressions.cross_sell
            else Decimal(0)
        )

        return ShopActivity.SectionDailyValue(upsell_ctr, cross_sell_ctr)

    def sales(self, created_at_date_range: CreatedAtDateRange) -> ShopActivity.SectionValue:
        upsell_conversions = UpsellConversion.objects.filter(
            upsell_impression__upsell_widget__shop__id=self.id, **created_at_date_range
        )
        upsell_sales = Decimal(sum([upsell_conversion.sales for upsell_conversion in upsell_conversions]))
        cross_sell_sales = Decimal(
            CrossSellConversion.objects.filter(purchase_shop_url=self.shop_url, **created_at_date_range).aggregate(
                models.Sum("sales")
            )["sales__sum"]
            or 0
        ).quantize(Decimal("0.01"))

        return ShopActivity.SectionValue(upsell_sales, cross_sell_sales)

    def total_sales(self, created_at_date_range: CreatedAtDateRange) -> ShopActivity.SectionCount:
        upsell_total_sales = UpsellConversion.objects.filter(
            upsell_impression__upsell_widget__shop__id=self.id, quantity__gt=0, **created_at_date_range
        ).count()
        cross_sell_total_sales = CrossSellConversion.objects.filter(
            purchase_shop_url=self.shop_url, **created_at_date_range
        ).count()

        return ShopActivity.SectionCount(upsell_total_sales, cross_sell_total_sales)

    def cr(
        self, total_sales: ShopActivity.SectionCount, clicks: ShopActivity.SectionCount
    ) -> ShopActivity.SectionValue:
        upsell_cr = 100 * (Decimal(total_sales.upsell) / Decimal(clicks.upsell)) if clicks.upsell else Decimal(0)
        cross_sell_cr = (
            100 * (Decimal(total_sales.cross_sell) / Decimal(clicks.cross_sell)) if clicks.cross_sell else Decimal(0)
        )

        return ShopActivity.SectionValue(upsell_cr, cross_sell_cr)

    def daily_activity(
        self, start_date: datetime, end_date: datetime, created_at_date_range: CreatedAtDateRange
    ) -> DailyActivity:
        daily_upsell_impressions = group_by_day(
            UpsellImpression.objects.filter(upsell_widget__shop__id=self.id, **created_at_date_range)
        )
        daily_cross_sell_impressions = group_by_day(
            CrossSellImpression.objects.filter(recommended_shop_urls__contains=[self.shop_url], **created_at_date_range)
        )

        daily_upsell_clicks = group_by_day(
            UpsellConversion.objects.filter(upsell_impression__upsell_widget__shop__id=self.id, **created_at_date_range)
        )
        daily_cross_sell_clicks = group_by_day(
            CrossSellClick.objects.filter(rdir__icontains=self.shop_url, **created_at_date_range)
        )

        daily_upsell_total_sales = group_by_day(
            UpsellConversion.objects.filter(
                upsell_impression__upsell_widget__shop__id=self.id, quantity__gt=0, **created_at_date_range
            )
        )
        daily_cross_sell_total_sales = group_by_day(
            CrossSellConversion.objects.filter(purchase_shop_url=self.shop_url, **created_at_date_range)
        )

        daily_upsell_sales = sum_by_day(
            UpsellConversion.objects.filter(
                upsell_impression__upsell_widget__shop__id=self.id, **created_at_date_range
            ),
            lambda x: x.sales,
        )
        daily_cross_sell_sales = sum_by_day(
            CrossSellConversion.objects.filter(purchase_shop_url=self.shop_url, **created_at_date_range),
            lambda x: x.sales,
        )

        daily_upsell_ctrs = {
            date: (
                100 * Decimal(daily_upsell_clicks.get(date, 0)) / Decimal(impressions)
                if impressions > 0
                else Decimal(0)
            )
            for date, impressions in daily_upsell_impressions.items()
        }
        daily_cross_sell_ctrs = {
            date: (
                100 * Decimal(daily_cross_sell_clicks.get(date, 0)) / Decimal(impressions)
                if impressions > 0
                else Decimal(0)
            )
            for date, impressions in daily_cross_sell_impressions.items()
        }

        daily_upsell_crs = {
            date: 100 * Decimal(daily_upsell_total_sales.get(date, 0)) / Decimal(clicks) if clicks > 0 else Decimal(0)
            for date, clicks in daily_upsell_clicks.items()
        }
        daily_cross_sell_crs = {
            date: (
                100 * Decimal(daily_cross_sell_total_sales.get(date, 0)) / Decimal(clicks) if clicks > 0 else Decimal(0)
            )
            for date, clicks in daily_cross_sell_clicks.items()
        }

        daily_infos = [
            daily_upsell_impressions,
            daily_cross_sell_impressions,
            daily_upsell_clicks,
            daily_cross_sell_clicks,
            daily_upsell_total_sales,
            daily_cross_sell_total_sales,
            daily_upsell_sales,
            daily_cross_sell_sales,
            daily_upsell_ctrs,
            daily_cross_sell_ctrs,
            daily_upsell_crs,
            daily_cross_sell_crs,
        ]

        for dt in daterange(start_date, end_date):
            date = str(dt.date())
            for daily_info in daily_infos:
                if date not in daily_info:
                    daily_info[date] = 0

        for daily_info in daily_infos:
            sorted_dict = dict(sorted(daily_info.items()))
            daily_info.clear()
            daily_info.update(sorted_dict)

        return (
            (
                ShopActivity.SectionDailyCount(
                    daily_upsell_impressions,
                    daily_cross_sell_impressions,
                ),
                ShopActivity.SectionDailyCount(
                    daily_upsell_clicks,
                    daily_cross_sell_clicks,
                ),
                ShopActivity.SectionDailyCount(
                    daily_upsell_total_sales,
                    daily_cross_sell_total_sales,
                ),
            ),
            (
                ShopActivity.SectionDailyValue(
                    daily_upsell_sales,
                    daily_cross_sell_sales,
                ),
                ShopActivity.SectionDailyValue(daily_upsell_ctrs, daily_cross_sell_ctrs),
                ShopActivity.SectionDailyValue(daily_upsell_crs, daily_cross_sell_crs),
            ),
        )

    def activity(self, start_date: datetime, end_date: datetime) -> ShopActivity:
        created_at_date_range = {"created_at__range": (start_date, end_date)}

        impressions = self.impressions(created_at_date_range)
        clicks = self.clicks(created_at_date_range)
        ctr = self.ctr(clicks, impressions)
        sales = self.sales(created_at_date_range)
        total_sales = self.total_sales(created_at_date_range)
        cr = self.cr(total_sales, clicks)
        daily_activity_counts, daily_activity_values = self.daily_activity(start_date, end_date, created_at_date_range)

        return ShopActivity(
            impressions,
            clicks,
            total_sales,
            sales,
            ctr,
            cr,
            *daily_activity_counts,
            *daily_activity_values,
        )
