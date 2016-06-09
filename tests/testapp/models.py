# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from six import python_2_unicode_compatible

from txmoney.money.models import MoneyField
from txmoney.money import Money
from txmoney.settings import txmoney_settings as settings


@python_2_unicode_compatible
class SimpleMoneyModel(models.Model):
    name = models.CharField(max_length=100)
    price = MoneyField(max_digits=12, decimal_places=3)

    def __str__(self):
        return self.name + ' ' + str(self.price)


@python_2_unicode_compatible
class MoneyModelDefaultMoneyUSD(models.Model):
    name = models.CharField(max_length=100)
    price = MoneyField(max_digits=12, decimal_places=3, default=Money('123.45', 'USD'))
    zero = MoneyField(max_digits=12, decimal_places=3, default=Money('0', 'USD'))

    def __str__(self):
        return self.name + ' ' + str(self.price)


@python_2_unicode_compatible
class MoneyModelDefaults(models.Model):
    name = models.CharField('Name', max_length=100)
    price = MoneyField('Price', max_digits=12, decimal_places=3, default='123.45', default_currency='USD')
    zero = MoneyField('Zero', max_digits=12, decimal_places=3, default='0', default_currency='USD')

    def __str__(self):
        return self.name + ' ' + str(self.price)


@python_2_unicode_compatible
class NullableMoneyModel(models.Model):
    name = models.CharField(max_length=100)
    price = MoneyField(max_digits=12, decimal_places=3, null=True)

    def __str__(self):
        return self.name + ' ' + str(self.price)


# A parametrized way of testing the model defaults. The following are all
# accetpable ways the field can be defined on a model
class ParametrizedModel(models.Model):
    """ The simplest possible declaration """
    value = MoneyField(max_digits=12, decimal_places=3, default=123)

    @staticmethod
    def expected_value():
        return Money('123', settings.BASE_CURRENCY)


class ParametrizedDefaultAsZeroMoneyModel(models.Model):
    """ The simplest possible declaration with a Money object """
    value = MoneyField(max_digits=12, decimal_places=3, default=Money(0, 'JPY'))

    @staticmethod
    def expected_value():
        return Money('0', 'JPY')


class ParametrizedDefaultAsMoneyModel(models.Model):
    """ The simplest possible declaration with a Money object """
    value = MoneyField(max_digits=12, decimal_places=3, default=Money(100, 'JPY'))

    @staticmethod
    def expected_value():
        return Money('100', 'JPY')


class ParametrizedDefaultAsZeroModel(models.Model):
    """ The simplest possible declaration with a zero default """
    value = MoneyField(max_digits=12, decimal_places=3, default=0)

    @staticmethod
    def expected_value():
        return Money('0', settings.BASE_CURRENCY)


class ParametrizedDefaultAsValueModel(models.Model):
    """ The simplest possible declaration with a non-zero default """
    value = MoneyField(max_digits=12, decimal_places=3, default=100)

    @staticmethod
    def expected_value():
        return Money('100', settings.BASE_CURRENCY)


class ParametrizedDefaultAsValueWithCurrencyModel(models.Model):
    """ The simplest possible declaration with a zero default """
    value = MoneyField(max_digits=12, decimal_places=3, default=0, default_currency='JPY')

    @staticmethod
    def expected_value():
        return Money('0', 'JPY')


class ParametrizedDefaultAsValueWithCurrencyAndLabelModel(models.Model):
    """ The simplest possible declaration with a zero default and a label """
    value = MoneyField('Value', max_digits=12, decimal_places=3, default=0, default_currency='JPY')

    @staticmethod
    def expected_value():
        return Money('0', 'JPY')


ALL_PARAMETRIZED_MODELS = [
    ParametrizedModel,
    ParametrizedDefaultAsZeroMoneyModel,
    ParametrizedDefaultAsMoneyModel,
    ParametrizedDefaultAsZeroModel,
    ParametrizedDefaultAsValueModel,
    ParametrizedDefaultAsValueWithCurrencyModel,
    ParametrizedDefaultAsValueWithCurrencyAndLabelModel,
]
