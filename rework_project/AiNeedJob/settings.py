"""
Django settings for the reworked AiNeedJob project.

This file is derived from the original project in the
`TopicosISTaller1` repository and has been slightly tidied up
for clarity.  It still uses the default SQLite database and
loads an OpenAI API key from an environment file.  See
README.md for more details.
"""

from pathlib import Path
import os
from dotenv import load_dotenv  # type: ignore

# Load environment variables from .env file for OpenAI API key
load_dotenv("openai_key.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Build paths inside the project
BASE_DIR: Path = Path(__file__).resolve().parent.parent
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-%%16hi4qwc%*(b=$@&bd(=!no+@g5ggq&&j8^nhu6mg@w109m&"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS: list[str] = ["127.0.0.1", "localhost"]

STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "CVapp",
    "offer",
    "users",
    "notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "AiNeedJob.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "AiNeedJob", "templates")],
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

WSGI_APPLICATION = "AiNeedJob.wsgi.application"

# Database configuration: SQLite for simplicity
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "es-co"  # localize for Colombia
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"