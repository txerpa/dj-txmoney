# coding=utf-8
from __future__ import absolute_import, division, unicode_literals

from datetime import date
from decimal import Decimal

from django.utils.six import iteritems

from ..settings import txmoney_settings as settings
from .models import Rate


def exchange_ratio(currency_from, currency_to, ratio_date=None):
    """
    Return exchange ratio between two currencies for a date
    """
    ratio_date = ratio_date or date.today()
    rate_from = rate_to = Decimal(1)

    if currency_from != currency_to:
        if currency_from != settings.BASE_CURRENCY:
            rate_from = Rate.objects.get_for_date(currency_from, ratio_date).value
        if currency_to != settings.BASE_CURRENCY:
            rate_to = Rate.objects.get_for_date(currency_to, ratio_date).value

    return rate_to / rate_from


def parse_rates_to_base_currency(rates, origin_currency):
    """
    Exchange rates dictionary in some currency to system currency.
    System currency *MUST* be present in the dictionary.
    """
    assert isinstance(rates, dict), "rates is not a dictionary"

    try:
        rate = Decimal(1) / rates[settings.BASE_CURRENCY]
    except KeyError:
        raise KeyError("System currency '%s' not found in rates dictionary", settings.BASE_CURRENCY)

    del rates[settings.BASE_CURRENCY]
    for currency, value in iteritems(rates):
        rates[currency] = value * rate
    rates[origin_currency] = rate

    return rates
