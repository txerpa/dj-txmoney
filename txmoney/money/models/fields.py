# coding=utf-8
from __future__ import absolute_import, unicode_literals

from decimal import Decimal

from django import VERSION
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Field
from django.db.models.expressions import (
    BaseExpression, Expression, F, Func, Value
)
from django.db.models.signals import class_prepared
from django.utils.six import string_types

from ...compat import setup_managers
from ...settings import txmoney_settings as settings
from ..exceptions import NotSupportedLookup
from .money import Currency, Money
from .utils import get_currency_field_name, prepare_expression

try:
    from django.utils.encoding import smart_unicode
except ImportError:
    from django.utils.encoding import smart_text as smart_unicode


__all__ = 'MoneyField'

SUPPORTED_LOOKUPS = ('exact', 'lt', 'gt', 'lte', 'gte', 'isnull', 'in')


def get_currency(value):
    """
    Extracts currency from value.
    """
    if isinstance(value, Money):
        return smart_unicode(value.currency)
    elif isinstance(value, (list, tuple)):
        return value[1]


def get_value(obj, expr):
    """
    Extracts value from object or expression.
    """
    if isinstance(expr, F):
        expr = getattr(obj, expr.name)
    elif hasattr(expr, 'value'):
        expr = expr.value
    return expr


def validate_lookup(lookup):
    if lookup not in SUPPORTED_LOOKUPS:
        raise NotSupportedLookup(lookup)


def validate_money_expression(obj, expr):
    """
    Money supports different types of expressions, but you can't do following:
      - Add or subtract money with not-money
      - Any exponentiation
      - Any operations with money in different currencies
      - Multiplication, division, modulo with money instances on both sides of expression
    """
    connector = expr.connector
    lhs = get_value(obj, expr.lhs)
    rhs = get_value(obj, expr.rhs)

    if (not isinstance(rhs, Money) and connector in ('+', '-')) or connector == '^':
        raise ValidationError('Invalid F expression for MoneyField.', code='invalid')
    if isinstance(lhs, Money) and isinstance(rhs, Money):
        if connector in ('*', '/', '^', '%%'):
            raise ValidationError('Invalid F expression for MoneyField.', code='invalid')
        if lhs.currency != rhs.currency:
            raise ValidationError('You cannot use F() with different currencies.', code='invalid')


def validate_money_value(value):
    """
    Valid value for money are:
      - Single numeric value
      - Money instances
      - Pairs of numeric value and currency. Currency can't be None.
    """
    if isinstance(value, (list, tuple)) and (len(value) != 2 or value[1] is None):
        raise ValidationError(
            'Invalid value for MoneyField: %(value)s.',
            code='invalid',
            params={'value': value},
        )


def setup_default(default, default_currency, nullable):
    if default is None and not nullable:
        # Backwards compatible fix for non-nullable fields
        default = '0.0'
    if isinstance(default, string_types):
        try:
            # handle scenario where default is formatted like:
            # 'amount currency-code'
            amount, currency = default.split(' ')
        except ValueError:
            # value error would be risen if the default is
            # without the currency part, i.e
            # 'amount'
            amount = default
            currency = default_currency
        default = Money(Decimal(amount), Currency(code=currency))
    elif isinstance(default, (float, Decimal, int)):
        default = Money(default, default_currency)
    if not (nullable and default is None) and not isinstance(default, Money):
        raise ValueError('Default value must be an instance of Money, is: %s' % default)
    return default


class MoneyFieldProxy(object):
    """
    An equivalent to Django's default attribute descriptor class SubfieldBase
    (normally enabled via `__metaclass__ = models.SubfieldBase` on the custom
    Field class).
    Instead of calling to_python() on our MoneyField class as SubfieldBase
    does, it stores the two different parts separately, and updates them
    whenever something is assigned. If the attribute is read, it builds the
    instance "on-demand" with the current data.
    See
    """

    def __init__(self, field):
        self.field = field
        self.currency_field_name = get_currency_field_name(field.name)

    def _money_from_obj(self, obj):
        amount_value = obj.__dict__[self.field.name]
        currency_value = obj.__dict__[self.currency_field_name]
        if amount_value is None:
            return None
        return Money(amount=amount_value, currency=currency_value)

    def __get__(self, obj, *args):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')
        data = obj.__dict__
        if isinstance(data[self.field.name], BaseExpression):
            return data[self.field.name]
        if not isinstance(data[self.field.name], Money):
            data[self.field.name] = self._money_from_obj(obj)
        return data[self.field.name]

    def __set__(self, obj, value):
        if isinstance(value, BaseExpression):
            if Value and isinstance(value, Value):
                value = self.prepare_value(obj, value.value)
            elif Func and isinstance(value, Func):
                pass
            else:
                validate_money_expression(obj, value)
                prepare_expression(value)
        else:
            value = self.prepare_value(obj, value)
        obj.__dict__[self.field.name] = value

    def prepare_value(self, obj, value):
        validate_money_value(value)
        currency = get_currency(value)
        if currency:
            self.set_currency(obj, currency)
        return self.field.to_python(value)

    def set_currency(self, obj, value):
        # we have to determine whether to replace the currency.
        # i.e. if we do the following:
        # .objects.get_or_create(money_currency='EUR')
        # then the currency is already set up, before this code hits
        # __set__ of MoneyField. This is because the currency field
        # has less creation counter than money field.
        object_currency = obj.__dict__[self.currency_field_name]
        if object_currency != value:
            # in other words, update the currency only if it wasn't
            # changed before.
            setattr(obj, self.currency_field_name, value)


class CurrencyField(models.CharField):
    """
    This field will be added to the model behind the scenes to hold the
    currency. It is used to enable outputting of currency data as a separate
    value when serializing to JSON.
    """

    def __init__(self, price_field=None, verbose_name=None, name=None, default=settings.DEFAULT_CURRENCY, **kwargs):
        if isinstance(default, Currency):
            default = default.code
        kwargs['max_length'] = 3
        self.price_field = price_field
        super(CurrencyField, self).__init__(verbose_name, name, default=default, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        if name not in [f.name for f in cls._meta.fields]:
            super(CurrencyField, self).contribute_to_class(cls, name, **kwargs)


class MoneyField(models.DecimalField):
    description = 'A field which stores both the currency and amount of money.'

    def __init__(self, verbose_name=None, name=None, max_digits=None, decimal_places=None, **kwargs):
        default_currency = kwargs.pop('default_currency', settings.DEFAULT_CURRENCY)
        # currency_choices = kwargs.pop('currency_choices', settings.CURRENCY_CHOICES)
        nullable = kwargs.get('null', False)
        default = kwargs.pop('default', None)
        default = setup_default(default, default_currency, nullable)
        if not default_currency:
            default_currency = default.currency

        self.default_currency = default_currency
        # self.currency_choices = currency_choices

        super(MoneyField, self).__init__(verbose_name, name, max_digits, decimal_places, default=default, **kwargs)
        self.creation_counter += 1
        Field.creation_counter += 1

    def to_python(self, value):
        if isinstance(value, Money):
            value = value.amount
        if isinstance(value, tuple):
            value = value[0]
        if isinstance(value, float):
            value = str(value)
        return super(MoneyField, self).to_python(value)

    def contribute_to_class(self, cls, name, **kwargs):
        cls._meta.has_money_field = True
        self.add_currency_field(cls, name)
        super(MoneyField, self).contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, MoneyFieldProxy(self))

    def add_currency_field(self, cls, name):
        """
        Adds CurrencyField instance to a model class.
        """
        kwargs = {
            'max_length': 3,
            'price_field': self,
            'default': self.default_currency,
            'editable': False
        }
        if self.db_column is not None:
            kwargs['db_column'] = get_currency_field_name(self.db_column)

        currency_field = CurrencyField(**kwargs)
        currency_field.creation_counter = self.creation_counter - 1
        currency_field_name = get_currency_field_name(name)
        cls.add_to_class(currency_field_name, currency_field)

    def get_db_prep_save(self, value, connection):
        if isinstance(value, Expression):
            return value
        if isinstance(value, Money):
            value = value.amount_rounded
        return super(MoneyField, self).get_db_prep_save(value, connection)

    def get_db_prep_lookup(self, lookup_type, value, connection, prepared=False):
        validate_lookup(lookup_type)
        value = self.get_db_prep_save(value, connection)
        return super(MoneyField, self).get_db_prep_lookup(lookup_type, value, connection, prepared)

    def get_lookup(self, lookup_name):
        validate_lookup(lookup_name)
        return super(MoneyField, self).get_lookup(lookup_name)

    def get_default(self):
        if isinstance(self.default, Money):
            return self.default
        return super(MoneyField, self).get_default()

    def value_to_string(self, obj):
        """
        When serializing this field, we will output both value and currency.
        Here we only need to output the value. The contributed currency field
        will get called to output itself
        """
        if VERSION < (2, 0):
            value = self._get_val_from_obj(obj)
        else:
            value = self.value_from_object(obj)
        return self.get_prep_value(value)


def patch_managers(sender, **kwargs):
    """
    Patches models managers.
    """
    if sender._meta.proxy_for_model:
        has_money_field = hasattr(sender._meta.proxy_for_model._meta, 'has_money_field')
    else:
        has_money_field = hasattr(sender._meta, 'has_money_field')

    if has_money_field:
        setup_managers(sender)


class_prepared.connect(patch_managers)
