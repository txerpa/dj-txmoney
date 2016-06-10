# coding=utf-8
from __future__ import absolute_import, unicode_literals

import os


DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DATABASE_NAME', 'txmoney'),
        'USER': os.environ.get('DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.get('DATABASE_PASS', 'postgres'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),

        'TEST': {
            'NAME': os.environ.get('DATABASE_NAME', None),
        }
    }
}

SECRET_KEY = 'not needed'

USE_TZ = True

MIDDLEWARE_CLASSES = ()

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',

    'rest_framework',

    'tests.testapp',
    'txmoney.rates',
    'txmoney.rest',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache',
    }
}

ROOT_URLCONF = 'tests.testapp.urls'

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

SITE_ID = 1

TXMONEY = {
    'BACKEND_KEY': os.environ.get('BACKEND_KEY'),
    'BASE_CURRENCY': 'EUR',
}
