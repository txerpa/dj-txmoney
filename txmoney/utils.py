# coding=utf-8
from __future__ import absolute_import, division, unicode_literals

from decimal import Decimal

from django.utils.six import iteritems

from txmoney.money.models.models import CURRENCIES
from txmoney.settings import txmoney_settings as settings


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


def clean_rates(rates):
    """
    Clean rates list to accept only system supported rates
    :param rates: rates currencies
    """
    intersection_rates = set(CURRENCIES).intersection(set(rates))

    for key in rates.keys():
        if key not in intersection_rates:
            del rates[key]

    return rates
