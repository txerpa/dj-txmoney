import sys

try:
    import pytest
    from django.conf import settings
    from django.test.utils import get_runner

    settings.configure(
        DEBUG=True,
        USE_TZ=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                'NAME': ':memory:'
            }
        },
        ROOT_URLCONF="tests.testapp.urls",
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sites",
            "txmoney",
            'tests.testapp'
        ],
        SITE_ID=1,
        MIDDLEWARE_CLASSES=(),
        TXMONEY={
            'BACKEND_KEY': 'bd1c4da0260242ad8807b2a8f0720750',  # TODO: anadir a variable de entorno
            'BASE_CURRENCY': 'USD',
        },
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
    raise ImportError("To fix this error, run: pip install -r requirements-test.txt")


def run_tests(*test_args):
    if not test_args:
        test_args = ['--cov-config', '.coveragerc', '--cov=txmoney', 'tests']

    failures = pytest.main(test_args)

    if failures:
        sys.exit(bool(failures))


if __name__ == '__main__':
    run_tests(*sys.argv[1:])
