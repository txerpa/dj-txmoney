# -*- coding: utf-8
from __future__ import absolute_import, unicode_literals

import os

import django

DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DATABASE_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DATABASE_NAME", "txmoney"),
        'USER': os.environ.get("DATABASE_USER", ""),
        'PASSWORD': os.environ.get("DATABASE_PASSWORD", ""),
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "rest_framework",
    "txmoney.rates.apps.TXMoneyConfig",
    "txmoney.rest.apps.TXMoneyRestAppConfig",
    "tests.testapp"
]

if django.VERSION >= (1, 10):
    MIDDLEWARE = ()
else:
    MIDDLEWARE_CLASSES = ()

ROOT_URLCONF = "tests.testapp.urls"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]

SECRET_KEY = "not needed"

SITE_ID = 1

TXMONEY = {
    "BACKEND_KEY": os.environ.get("BACKEND_KEY"),
    "BASE_CURRENCY": "EUR",
}

USE_TZ = True
