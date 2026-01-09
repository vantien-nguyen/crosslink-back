from django.urls import path
from shopify_app import views

app_name = "shopify"

urlpatterns = [
    path("login/", views.shopify_login, name="shopify_app_login"),
    path("authenticate/", views.authenticate, name="shopify_app_authenticate"),
    path("finalize/", views.finalize, name="shopify_app_finalize"),
    path("cross-sell-widget/", views.cross_sell_widget, name="shopify_app_cross_sell_widget"),
    path("upsell/offer/", views.upsell_offer, name="shopify_app_upsell_offer"),
    path(
        "upsell/sign-changeset/",
        views.sign_changeset,
        name="shopify_app_upsell_sign_changeset",
    ),
    path("webhook/product/create", views.product_create, name="product_create"),
    path("webhook/product/update", views.product_update, name="product_update"),
    path("webhook/product/delete", views.product_delete, name="product_delete"),
]
