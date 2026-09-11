import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-key-change-me")

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

_allowed_hosts = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = _allowed_hosts.split(",") if _allowed_hosts != "*" else ["*"]

FORCE_SCRIPT_NAME = os.environ.get("DJANGO_FORCE_SCRIPT_NAME") or None

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# No accounts, no auth, no sessions, no database: this is a single
# static hello-world page, same architectural pattern as Kaliptus/Dantinea.
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "vibenight",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = f"{os.environ.get('DJANGO_FORCE_SCRIPT_NAME', '')}/static/"
STATIC_ROOT = os.environ.get("VIBENIGHT_STATIC_ROOT", str(BASE_DIR / "staticfiles"))

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Append-only log for the consent-gated keylogging course exercise (see
# vibenight/views.py's keylog_ingest) — same pattern as transfer.sh's
# events.jsonl rather than a real database.
VIBENIGHT_KEYLOG_PATH = os.environ.get("VIBENIGHT_KEYLOG_PATH", str(BASE_DIR / "keylog.jsonl"))
