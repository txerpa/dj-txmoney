# coding=utf-8
from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta
from decimal import Decimal

from mock import patch
from tests.factories import RateFactory, RateSourceFactory

from django.test import TestCase

from txmoney.exceptions import RateDoesNotExist
from txmoney.models import Rate
from txmoney.settings import txmoney_settings as settings


class TestRateSource(TestCase):

    def setUp(self):
        self.rs = RateSourceFactory.create()

    def test_is_updated(self):
        self.assertTrue(self.rs.is_updated)

    def test_not_is_updated(self):
        with patch.object(self.rs, 'last_update', return_value=datetime.now() - timedelta(1)):
            return self.assertFalse(self.rs.is_updated)


class TestRate(TestCase):

    def setUp(self):
        self.c1 = RateFactory.create()
        self.c2 = RateFactory.create()

    def test_get_ratio(self):
        ratio_base_other = Rate.get_ratio(settings.BASE_CURRENCY, self.c1.currency)
        ratio_other_base = Rate.get_ratio(self.c1.currency, settings.BASE_CURRENCY)
        ratio_base_base = Rate.get_ratio(settings.BASE_CURRENCY, settings.BASE_CURRENCY)
        ratio_other_other = Rate.get_ratio(self.c1.currency, self.c2.currency)

        self.assertTrue(ratio_base_other, 1 / self.c1.value)
        self.assertTrue(ratio_other_base, self.c1.value)
        self.assertTrue(ratio_base_base, Decimal(1))
        self.assertTrue(ratio_other_other, self.c1.value * Decimal(1) / self.c2.value)

    def test_get_ratio_error(self):
        with self.assertRaises(RateDoesNotExist):
            Rate.get_ratio(settings.BASE_CURRENCY, 'XXX')
