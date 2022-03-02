# coding=utf-8

from datetime import date
from decimal import Decimal

from six import iteritems

from ..settings import txmoney_settings
from .models import Rate


def exchange_ratio(currency_from, currency_to, ratio_date=None):
    """
    Return exchange ratio between two currencies for a date
    """
    ratio_date = ratio_date or date.today()
    rate_from = rate_to = Decimal(1)

    if currency_from != currency_to:
        if currency_from != txmoney_settings.DEFAULT_CURRENCY:
            rate_from = Rate.objects.get_for_date(currency_from, ratio_date).value
        if currency_to != txmoney_settings.DEFAULT_CURRENCY:
            rate_to = Rate.objects.get_for_date(currency_to, ratio_date).value

    return rate_to / rate_from


def parse_rates_to_base_currency(rates, origin_currency):
    """
    Exchange rates dictionary in some currency to system currency.
    System currency *MUST* be present in the dictionary.
    """
    assert isinstance(rates, dict), "rates is not a dictionary"

    try:
        rate = Decimal(1) / rates[txmoney_settings.DEFAULT_CURRENCY]
    except KeyError:
        raise KeyError(f'System currency "{txmoney_settings.DEFAULT_CURRENCY}" not found in rates dictionary')

    del rates[txmoney_settings.DEFAULT_CURRENCY]
    for currency, value in iteritems(rates):
        rates[currency] = value * rate
    rates[origin_currency] = rate

    return rates
