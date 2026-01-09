import os
from datetime import timedelta

from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "home"

    def ready(self):
        # Import Elasticsearch documents so they get registered on startup.
        from home.documents import products  # noqa: F401

    # --- General ---
    APP_HOST = os.environ.get("APP_HOST")
    CLIENT_APP_HOST = os.environ.get("CLIENT_APP_HOST")
    ENVIRONMENT = os.environ.get("ENVIRONMENT")
    CLIENT_LOGIN_ROUTE = "login"
    CLIENT_SIGNUP_ROUTE = "signup"

    # --- Security ---
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # --- AWS ---
    AWS_REGION = os.environ.get("AWS_REGION")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
    S3_UPLOAD_ATTACHMENT_PRESIGNED_URL_EXPIRY = timedelta(seconds=120)

    # --- Redis ---
    REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    REDIS_DB = int(os.environ.get("REDIS_DB", 0))
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

    @classmethod
    def is_local(cls):
        return cls.ENVIRONMENT == "local"

    @classmethod
    def is_staging(cls):
        return cls.ENVIRONMENT == "testing"

    @classmethod
    def is_production(cls):
        return cls.ENVIRONMENT == "production"
