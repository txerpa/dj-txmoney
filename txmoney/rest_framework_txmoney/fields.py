# coding=utf-8
from __future__ import absolute_import, unicode_literals

from rest_framework.fields import Field, SerializerMethodField
from six import string_types

from txmoney.money import Money


class MoneyField(Field):
    """
    A field to handle TXMoney money fields
    """
    type_name = 'MoneyField'

    def __init__(self, **kwargs):
        super(MoneyField, self).__init__(**kwargs)

    def to_representation(self, value):
        return value.amount

    def to_internal_value(self, value):
        if isinstance(value, string_types):
            try:
                (value, currency) = value.split()
                if value and currency:
                    return Money(value, currency)
            except ValueError:
                pass
        return value


class MoneySerializerMethodField(SerializerMethodField):
    def to_internal_value(self, value):
        if isinstance(value, string_types):
            try:
                (value, currency) = value.split()
                if value and currency:
                    return Money(value, currency)
            except ValueError:
                pass
        return value

    def to_representation(self, value):
        value = super(MoneySerializerMethodField, self).to_representation(value)
        if value is not None:
            return value.amount
        return value
