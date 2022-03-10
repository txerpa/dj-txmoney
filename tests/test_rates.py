import time
import json

from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase

from txmoney.rates.models import Rate, RateSource
from txmoney.rates.tasks import update_rates

try:
    from mock import patch
except NameError:
    from unittest.mock import patch


class TestRateSource(TestCase):
    def setUp(self):
        self.rs = RateSource.objects.create(name="Test source", base_currency="EUR")

    def test_is_updated(self):
        self.assertTrue(self.rs.is_updated)

    def test_not_is_updated(self):
        with patch.object(
            self.rs, "last_update", return_value=datetime.now() - timedelta(1)
        ):
            return self.assertFalse(self.rs.is_updated)


class TestRate(TestCase):
    def setUp(self):
        rs = RateSource.objects.create(name="Test source")
        self.c1 = Rate.objects.create(
            source=rs, currency="GBP", value=Decimal("1.1176")
        )
        self.c2 = Rate.objects.create(
            source=rs, currency="MXN", value=Decimal("0.054069")
        )


def rates():
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self, parse_float):
            return json.loads(self.json_data, parse_float=parse_float)

    return MockResponse(
        """
        {
          "base": "USD",
          "rates": {
            "BRL": 5.011,
            "EUR": 0.905768,
            "GBP": 0.759922
          }
        }
        """,
        200,
    )


class TestTasks(TestCase):
    @patch("requests.get")
    def test_update_rates_task(self, get_rates_mock):
        get_rates_mock.return_value = rates()

        update_rates()
        get_rates_mock.assert_called_once()
