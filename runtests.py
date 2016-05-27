# coding=utf-8
import sys

try:
    from django.conf import settings
    import pytest

    settings.configure(
        DEBUG=True,
        USE_TZ=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sites',
            'txmoney',
        ],
        SITE_ID=1,
        MIDDLEWARE_CLASSES=(),
        TXMONEY={
            'BACKEND_KEY': 'bd1c4da0260242ad8807b2a8f0720750'  # TODO: añadir a variable de entorno
        }
    )

    try:
        import django
        setup = django.setup
    except AttributeError:
        pass
    else:
        setup()

except ImportError:
    import traceback
    traceback.print_exc()
    raise ImportError('To fix this error, run: pip install -r requirements-test.txt')


def run_tests(*test_args):
    if not test_args:
        test_args = ['tests']

    # Run tests
    failures = pytest.main(test_args)

    if failures:
        sys.exit(bool(failures))


if __name__ == '__main__':
    run_tests(*sys.argv[1:])
