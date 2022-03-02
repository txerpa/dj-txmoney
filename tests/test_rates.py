# coding=utf-8

from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase

from txmoney.rates.models import Rate, RateSource

try:
    from mock import patch
except NameError:
    from unittest.mock import patch


class TestRateSource(TestCase):

    def setUp(self):
        self.rs = RateSource.objects.create(name='Test source', base_currency='EUR')

    def test_is_updated(self):
        self.assertTrue(self.rs.is_updated)

    def test_not_is_updated(self):
        with patch.object(self.rs, 'last_update', return_value=datetime.now() - timedelta(1)):
            return self.assertFalse(self.rs.is_updated)


class TestRate(TestCase):

    def setUp(self):
        rs = RateSource.objects.create(name='Test source')
        self.c1 = Rate.objects.create(source=rs, currency='GBP', value=Decimal('1.1176'))
        self.c2 = Rate.objects.create(source=rs, currency='MXN', value=Decimal('0.054069'))
