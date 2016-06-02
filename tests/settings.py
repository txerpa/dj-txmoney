# Settings to be used when running tests
import os

TEST_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)))

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(TEST_DIR, 'static')

DEBUG = True
USE_TZ = True
SECRET_KEY = 'abcde12345'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}
INSTALLED_APPS = [
    'txmoney',
    'tests.testapp'
]
CACHES = {
    # No cache
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

TXMONEY = {
    'BACKEND_KEY': 'bd1c4da0260242ad8807b2a8f0720750',  # TODO: anadir a variable de entorno
    'BASE_CURRENCY': 'USD',
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
)

ROOT_URLCONF = 'tests.testapp.urls'
