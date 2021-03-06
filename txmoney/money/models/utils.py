# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.db.models import F
from django.db.models.expressions import BaseExpression

from .money import Money


def get_currency_field_name(name):
    return "{}_currency".format(name)


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
    amount = get_amount(expr.rhs)
    expr.rhs.value = amount
    return expr.lhs
