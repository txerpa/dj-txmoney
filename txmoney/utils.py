# coding=utf-8
from __future__ import absolute_import, unicode_literals

from decimal import Decimal

from six import iteritems

from django.db.models.expressions import BaseExpression, F

from .money import CURRENCIES, Money
from .settings import txmoney_settings as settings


def parse_rates_to_base_currency(rates, rates_currency):
    """
    Exchange rates list to system base currency
    :param rates: rates list
    :param rates_currency: list base currency
    """
    rate = Decimal(1) / rates[rates_currency]  # TODO: utilizar funcion get ratio

    del rates[rates_currency]
    for currency, value in iteritems(rates):
        rates[currency] = value * rate
    rates[settings.BASE_CURRENCY] = rate

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


def get_currency_field_name(name):
    return "%s_currency" % name


def get_amount(value):
    """
    Extracts decimal value from Money or Expression.
    """
    if isinstance(value, Money):
        return value.amount
    elif isinstance(value, BaseExpression) and not isinstance(value, F):
        return get_amount(value.value)
    return value


def prepare_expression(expr):
    """
    Prepares some complex money expression to be used in query.
    """
    lhs, rhs = expr.lhs, expr.rhs
    amount = get_amount(rhs)
    expr.rhs.value = amount
    return lhs
