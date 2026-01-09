from django.urls import path
from django.urls.conf import include
from home.views import (
    CrossSellWidgetViewSet,
    DashboardViewSet,
    ProductViewSet,
    ShopViewSet,
    UpsellWidgetViewSet,
    health,
)
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"dashboard", DashboardViewSet, basename="dashboard")
router.register(r"upsell-widgets", UpsellWidgetViewSet, basename="upsell-widgets")
router.register(r"products", ProductViewSet, basename="products")
router.register(r"cross-sell-widgets", CrossSellWidgetViewSet, basename="cross-sell-widgets")
router.register(r"shops", ShopViewSet, basename="shops")

urlpatterns = [
    path("", include(router.urls)),
    path("health", health),
]
