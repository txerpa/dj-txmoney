# coding=utf-8
from __future__ import absolute_import, unicode_literals

from datetime import date
from decimal import Decimal

from django.db import models
from django.utils.functional import cached_property

from ..settings import txmoney_settings as settings
from .exceptions import RateDoesNotExist


class RateSource(models.Model):
    name = models.CharField(max_length=100)
    base_currency = models.CharField(max_length=3, default=settings.BASE_CURRENCY, blank=True)
    last_update = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        unique_together = ('name', 'base_currency')

    @cached_property
    def is_updated(self):
        return True if self.last_update.date() == date.today() else False


class RateQuerySet(models.QuerySet):

    def get_rate_currency_by_date(self, currency, currency_date=None):
        """
        Get currency for a date
        :param currency: base currency.
        :param currency_date: rate currency date.
        :return: Currency
        """
        currency_date = currency_date if currency_date else date.today()
        try:
            backend = settings.DEFAULT_BACKEND()
            backend.update_rates()  # Only update if backend is not updated
            return self.filter(currency=currency, date__lte=currency_date).order_by('-date')[:1].get()
        except Rate.DoesNotExist:
            raise RateDoesNotExist(currency, currency_date)


class Rate(models.Model):
    source = models.ForeignKey(RateSource, on_delete=models.PROTECT, related_name='rates', related_query_name='rate')
    currency = models.CharField(max_length=3)
    value = models.DecimalField(max_digits=14, decimal_places=6)
    date = models.DateField(auto_now_add=True, blank=True, db_index=True)

    objects = RateQuerySet.as_manager()

    class Meta:
        unique_together = ('source', 'currency', 'date')

    @staticmethod
    def get_ratio(from_currency, to_currency, ratio_date=None):
        """
        Calculate exchange ratio between two currencies for a date
        :param from_currency: base currency.
        :param to_currency: ratio currency.
        :param ratio_date: ratio date
        :return: Decimal
        """
        ratio_date = ratio_date if ratio_date else date.today()
        # If not default currency get date base currency rate value because all rates are for base currency
        ratio = Decimal(1) if from_currency == settings.BASE_CURRENCY else \
            Rate.objects.get_rate_currency_by_date(from_currency, ratio_date).value

        if to_currency != settings.BASE_CURRENCY:
            money_rate = Decimal(1) / Rate.objects.get_rate_currency_by_date(to_currency, ratio_date).value
            ratio *= money_rate

        return ratio
