from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("home.urls")),
    path("api/users/", include("users.urls", namespace="users")),
    path("api/shopify/", include("shopify_app.urls", namespace="shopify")),
]
