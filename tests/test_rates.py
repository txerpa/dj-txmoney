# coding=utf-8
from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase

from txmoney.rates.exceptions import RateDoesNotExist
from txmoney.rates.models import Rate, RateSource
from txmoney.settings import txmoney_settings as settings


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

    def test_get_ratio(self):
        ratio_base_other = Rate.get_ratio(settings.BASE_CURRENCY, self.c1.currency)
        ratio_other_base = Rate.get_ratio(self.c1.currency, settings.BASE_CURRENCY)
        ratio_base_base = Rate.get_ratio(settings.BASE_CURRENCY, settings.BASE_CURRENCY)
        ratio_other_other = Rate.get_ratio(self.c1.currency, self.c2.currency)

        self.assertTrue(ratio_base_other, 1 / Decimal('1.1176'))
        self.assertTrue(ratio_other_base, Decimal('1.1176'))
        self.assertTrue(ratio_base_base, Decimal(1))
        self.assertTrue(ratio_other_other, Decimal('1.1176') * Decimal(1) / Decimal('0.054069'))

    def test_get_ratio_error(self):
        with self.assertRaises(RateDoesNotExist):
            Rate.get_ratio(settings.BASE_CURRENCY, 'XXX')
