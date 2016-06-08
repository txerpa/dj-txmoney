# coding=utf-8
from __future__ import absolute_import, unicode_literals

from decimal import Decimal

from django.db import models
from django.db.models import QuerySet

from six import string_types

from ...settings import txmoney_settings as settings
from ...utils import currency_field_name
from ..exceptions import NotSupportedLookup
from ..money import Money


def currency_field_db_column(db_column):
    return None if db_column is None else '{}_currency'.format(db_column)


SUPPORTED_LOOKUPS = ('exact', 'lt', 'gt', 'lte', 'gte', 'isnull')


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
        self.amount_field_name = field.name
        self.currency_field_name = currency_field_name(field.name)

    def _get_values(self, obj):
        return (
            obj.__dict__.get(self.field.amount_field_name, None), obj.__dict__.get(self.field.currency_field_name, None)
        )

    def _set_values(self, obj, amount, currency):
        obj.__dict__[self.field.amount_field_name] = amount
        obj.__dict__[self.field.currency_field_name] = currency

    def __get__(self, obj, *args):
        amount, currency = self._get_values(obj)
        if amount is None:
            return None
        return Money(amount, currency)

    def __set__(self, obj, value):
        if value is None:  # Money(0) is False
            self._set_values(obj, None, '')
        elif isinstance(value, Money):
            self._set_values(obj, value.amount, value.currency)
        elif isinstance(value, Decimal):
            _, currency = self._get_values(obj)  # use what is currently set
            self._set_values(obj, value, currency)
        else:
            # It could be an int, or some other python native type
            try:
                amount = Decimal(str(value))
                _, currency = self._get_values(obj)  # use what is currently set
                self._set_values(obj, amount, currency)
            except TypeError:
                try:
                    _, currency = self._get_values(obj)  # use what is currently set
                    m = Money.from_string(str(value))
                    self._set_values(obj, m.amount, m.currency)
                except TypeError:
                    msg = 'Cannot assign "{}"'.format(type(value))
                    raise TypeError(msg)


class CurrencyField(models.CharField):
    """
    This field will be added to the model behind the scenes to hold the
    currency. It is used to enable outputting of currency data as a separate
    value when serializing to JSON.
    """

    def value_to_string(self, obj):
        """
        When serializing, we want to output as two values. This will be just
        the currency part as stored directly in the database.
        """
        value = self._get_val_from_obj(obj)
        return value


class InfiniteDecimalField(models.DecimalField):
    def db_type(self, connection):
        engine = connection.settings_dict['ENGINE']

        if 'postgresql' in engine:
            return 'numeric'

        return super(InfiniteDecimalField, self).db_type(connection=connection)

    def get_db_prep_save(self, value, *args, **kwargs):
        # The superclass DecimalField get_db_prep_save will add decimals up to
        # the precision in the field definition. The point of this class is to
        # use the user-specified precision up to that limit instead. For that
        # reason we will call get_db_prep_value instead
        return self.get_db_prep_value(value, *args, **kwargs)


class MoneyField(InfiniteDecimalField):
    description = 'A field which stores both the currency and amount of money.'

    def __init__(self, *args, **kwargs):
        default_currency = kwargs.pop('default_currency', settings.BASE_CURRENCY)
        default = kwargs.get('default', None)
        self.blankable = kwargs.get('blank', False)

        if isinstance(default, Money):
            self.default_currency = default.currency  # use the default's currency
            kwargs['default'] = default.amount
        else:
            self.default_currency = default_currency

        super(MoneyField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(MoneyField, self).deconstruct()
        return name, path, args, kwargs

    def to_python(self, value):
        if isinstance(value, string_types):
            try:
                (value, currency) = value.split()
                if value and currency:
                    return Money(value, currency)
            except ValueError:
                pass
        return value

    def contribute_to_class(self, cls, name):
        self.name = name
        self.amount_field_name = name
        self.currency_field_name = currency_field_name(name)

        if not cls._meta.abstract:
            c_field = CurrencyField(
                max_length=3,
                default=self.default_currency,
                editable=False,
                null=False,  # empty char fields should be ''
                blank=self.blankable,
                db_column=currency_field_db_column(self.db_column),
            )
            # Use this field's creation counter for the currency field. This
            # field will get a +1 when we call super
            c_field.creation_counter = self.creation_counter
            cls.add_to_class(self.currency_field_name, c_field)

        # Set ourselves up normally
        super(MoneyField, self).contribute_to_class(cls, name)

        # As we are not using SubfieldBase, we need to set our proxy class here
        setattr(cls, self.name, MoneyFieldProxy(self))

        # Set our custom manager
        if not hasattr(cls, '_default_manager'):
            cls.add_to_class('objects', MoneyManager())

    def get_db_prep_save(self, value, *args, **kwargs):
        if isinstance(value, Money):
            value = value.amount_rounded

        return super(MoneyField, self).get_db_prep_save(value, *args, **kwargs)

    def get_prep_lookup(self, lookup_type, value):
        if lookup_type not in SUPPORTED_LOOKUPS:
            raise NotSupportedLookup(lookup_type)

        if isinstance(value, Money):
            value = value.amount

        return super(MoneyField, self).get_prep_lookup(lookup_type, value)

    def get_default(self):
        if isinstance(self.default, Money):
            return self.default
        else:
            return super(MoneyField, self).get_default()

    def value_to_string(self, obj):
        """
        When serializing this field, we will output both value and currency.
        Here we only need to output the value. The contributed currency field
        will get called to output itself
        """
        value = self._get_val_from_obj(obj)
        return value.amount


class QuerysetWithMoney(QuerySet):
    def _update_params(self, kwargs):
        from django.db.models.constants import LOOKUP_SEP
        from txmoney.money.money import Money
        to_append = {}
        for name, value in kwargs.items():
            if isinstance(value, Money):
                path = name.split(LOOKUP_SEP)
                if len(path) > 1:
                    field_name = currency_field_name(path[0])
                else:
                    field_name = currency_field_name(name)
                to_append[field_name] = value.currency
        kwargs.update(to_append)
        return kwargs

    def dates(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).dates(*args, **kwargs)

    def distinct(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).distinct(*args, **kwargs)

    def extra(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).extra(*args, **kwargs)

    def get(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).get(*args, **kwargs)

    def get_or_create(self, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).get_or_create(**kwargs)

    def filter(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).filter(*args, **kwargs)

    def complex_filter(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).complex_filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).exclude(*args, **kwargs)

    def in_bulk(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).in_bulk(*args, **kwargs)

    def iterator(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).iterator(*args, **kwargs)

    def latest(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).latest(*args, **kwargs)

    def order_by(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).order_by(*args, **kwargs)

    def select_related(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).select_related(*args, **kwargs)

    def values(self, *args, **kwargs):
        kwargs = self._update_params(kwargs)
        return super(QuerysetWithMoney, self).values(*args, **kwargs)


class MoneyManager(models.Manager):
    def get_queryset(self):
        return QuerysetWithMoney(self.model)
