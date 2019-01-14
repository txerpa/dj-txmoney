# coding=utf-8

from decimal import Decimal

from django.db import models

from txmoney.money.models.fields import MoneyField
from txmoney.money.models.managers import money_manager, understands_money
from txmoney.money.models.money import Money


class SimpleMoneyModel(models.Model):
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency='EUR')


class ModelWithDefaultAsString(models.Model):
    amount = MoneyField(default='123', max_digits=10, decimal_places=2, default_currency='PLN')


class ModelWithDefaultAsInt(models.Model):
    amount = MoneyField(default=123, max_digits=10, decimal_places=2, default_currency='GHS')


class ModelWithDefaultAsFloat(models.Model):
    amount = MoneyField(default=12.05, max_digits=10, decimal_places=2, default_currency='PLN')


class ModelWithDefaultAsDecimal(models.Model):
    amount = MoneyField(default=Decimal('0.01'), max_digits=10, decimal_places=2, default_currency='CHF')


class ModelWithDefaultAsMoney(models.Model):
    amount = MoneyField(default=Money('0.01', 'RUB'), max_digits=10, decimal_places=2)


class ModelWithDefaultAsStringWithCurrency(models.Model):
    amount = MoneyField(default='123 EUR', max_digits=10, decimal_places=2)


class NullMoneyFieldModel(models.Model):
    amount = MoneyField(max_digits=10, decimal_places=2, null=True, default_currency='EUR', blank=True)


class ModelWithTwoMoneyFields(models.Model):
    amount1 = MoneyField(max_digits=10, decimal_places=2)
    amount2 = MoneyField(max_digits=10, decimal_places=3)


# class ModelWithChoicesMoneyField(models.Model):
#     money = MoneyField(
#         max_digits=10,
#         decimal_places=2,
#         currency_choices=[
#             ('USD', 'US Dollars'),
#             ('GBP', 'British Pounds')
#         ],
#     )

class ModelRelatedToModelWithMoney(models.Model):
    money_model = models.ForeignKey(SimpleMoneyModel, on_delete=models.CASCADE)


class AbstractMoneyModel(models.Model):
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
    m2m_field = models.ManyToManyField(ModelWithDefaultAsInt)

    class Meta:
        abstract = True


class InheritorMoneyModel(AbstractMoneyModel):
    amount2 = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')


class InheritedMoneyModel(SimpleMoneyModel):
    amount2 = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')


class ProxyMoneyModel(SimpleMoneyModel):

    class Meta:
        proxy = True


class MoneyManager(models.Manager):

    @understands_money
    def super_method(self, **kwargs):
        return self.filter(**kwargs)


class ModelWithCustomManager(models.Model):
    field = MoneyField(max_digits=10, decimal_places=2)

    manager = money_manager(MoneyManager())
