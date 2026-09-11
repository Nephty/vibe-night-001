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

# Real DB + django.contrib.admin power the read-only keylog dashboard
# (see vibenight/admin.py) — the rest of the app (hello-world page, sudoku)
# still has no accounts of its own, only a single admin superuser.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "vibenight",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
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
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(os.environ.get("VIBENIGHT_DB_PATH", str(BASE_DIR / "db.sqlite3"))),
    },
}

CSRF_TRUSTED_ORIGINS = ["https://vibe-night.nephty.top"]

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

# Legacy append-only path for the keylogging course exercise, still read by
# the one-time import management command (vibenight/management/commands/
# import_keylog_jsonl.py) that backfilled KeylogEntry rows from it. The
# capture endpoint itself now writes straight to the DB.
VIBENIGHT_KEYLOG_PATH = os.environ.get("VIBENIGHT_KEYLOG_PATH", str(BASE_DIR / "keylog.jsonl"))
