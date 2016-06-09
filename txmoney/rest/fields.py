# coding=utf-8
from __future__ import absolute_import, unicode_literals

from rest_framework.fields import Field
from six import string_types

from txmoney.money import Money


class MoneyField(Field):
    """
    A field to handle TXMoney money fields
    """
    type_name = 'MoneyField'

    def __init__(self, max_digits, decimal_places, rounded=False, **kwargs):
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        self.rounded = rounded

        if self.max_digits is not None and self.decimal_places is not None:
            self.max_whole_digits = self.max_digits - self.decimal_places
        else:
            self.max_whole_digits = None

        super(MoneyField, self).__init__(**kwargs)

    def to_internal_value(self, value):
        if isinstance(value, string_types):
            try:
                (value, currency) = value.split()
                if value and currency:
                    value = Money(value, currency)
            except ValueError:
                self.fail('invalid')
        else:
            value = Money(value)

        return self.validate_precision(value)

    def to_representation(self, value):
        if not self.rounded:
            return value.amount
        return value.amount_rounded

    def validate_precision(self, value):
        """
        Ensure that there are no more than max_digits in the number, and no
        more than decimal_places digits after the decimal point.

        Override this method to disable the precision validation for input
        values or to enhance it in any way you need to.
        """
        sign, digittuple, exponent = value.amount.as_tuple()

        if exponent >= 0:
            # 1234500.0
            total_digits = len(digittuple) + exponent
            whole_digits = total_digits
            decimal_places = 0
        elif len(digittuple) > abs(exponent):
            # 123.45
            total_digits = len(digittuple)
            whole_digits = total_digits - abs(exponent)
            decimal_places = abs(exponent)
        else:
            # 0.001234
            total_digits = abs(exponent)
            whole_digits = 0
            decimal_places = total_digits

        if self.max_digits is not None and total_digits > self.max_digits:
            self.fail('max_digits', max_digits=self.max_digits)
        if self.decimal_places is not None and decimal_places > self.decimal_places:
            self.fail('max_decimal_places', max_decimal_places=self.decimal_places)
        if self.max_whole_digits is not None and whole_digits > self.max_whole_digits:
            self.fail('max_whole_digits', max_whole_digits=self.max_whole_digits)

        return value
