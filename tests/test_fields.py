# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.db import IntegrityError

import pytest

from txmoney.money.exceptions import NotSupportedLookup
from txmoney.money.money import CURRENCIES, Money
from txmoney.settings import txmoney_settings as settings

from .testapp.models import ALL_PARAMETRIZED_MODELS, MoneyModelDefaults, NullableMoneyModel, SimpleMoneyModel


def assertsamecurrency(moneys, currency_code=None):
    """ Utility function to assert a collection of currencies are all the same """
    currency_codes = set([m.currency.code for m in moneys])
    assert len(currency_codes) == 1
    if currency_code:
        assert currency_codes.pop() == currency_code


@pytest.mark.django_db
class TestMoneyField(object):
    def test_non_null(self):
        instance = SimpleMoneyModel()
        with pytest.raises(IntegrityError):
            instance.save()

    def test_creating(self):
        ind = 0
        for code, currency in CURRENCIES.items():
            ind += 1
            price = Money(ind * 1000.0, code)
            SimpleMoneyModel.objects.create(name=currency.name, price=price.amount, price_currency=price.currency)
        assert len(CURRENCIES) == SimpleMoneyModel.objects.all().count()

        for code in CURRENCIES:
            assert SimpleMoneyModel.objects.filter(price_currency=code).count() == 1

    def test_retrive(self):
        price = Money(100, 'USD')
        SimpleMoneyModel.objects.create(name='one hundred dollars', price=price)

        # Filter
        qset = SimpleMoneyModel.objects.filter(price=price)
        assert qset.count() == 1
        assert qset[0].price == price

        # Get
        entry = SimpleMoneyModel.objects.get(price=price)
        assert entry.price == price

        # test retrieving without currency
        entry = SimpleMoneyModel.objects.get(price=100)
        assert entry.price == price

    def test_assign(self):
        price = Money(100, 'USD')
        ent = SimpleMoneyModel(name='test', price=price.amount, price_currency=price.currency)
        ent.save()
        assert ent.price == Money(100, 'USD')

        ent.price = Money(10, 'USD')
        ent.save()
        assert ent.price == Money(10, 'USD')

        ent_same = SimpleMoneyModel.objects.get(pk=ent.id)
        assert ent_same.price == Money(10, 'USD')

    def test_retrieve_and_update(self):
        created = SimpleMoneyModel.objects.create(name='one hundred dollars', price=Money(100, 'USD'))
        created.save()
        assert created.price == Money(100, 'USD')

        ent = SimpleMoneyModel.objects.filter(price__exact=Money(100, 'USD')).get()
        assert ent.price == Money(100, 'USD')

        ent.price = Money(300, 'USD')
        ent.save()

        ent = SimpleMoneyModel.objects.filter(price__exact=Money(300, 'USD')).get()
        assert ent.price == Money(300, 'USD')

    def test_defaults_as_separate_values(self):
        ent = MoneyModelDefaults.objects.create(name='100 USD', price=100)
        assert ent.price == Money(100, 'USD')

        ent = MoneyModelDefaults.objects.get(pk=ent.id)
        assert ent.price == Money(100, 'USD')

    def test_lookup(self):
        usd100 = Money(100, 'USD')
        eur100 = Money(100, 'EUR')
        uah100 = Money(100, 'UAH')

        SimpleMoneyModel.objects.create(name='one hundred dollars', price=usd100)
        SimpleMoneyModel.objects.create(name='one hundred and one dollars', price=usd100 + 1)
        SimpleMoneyModel.objects.create(name='ninety nine dollars', price=usd100 - 1)

        SimpleMoneyModel.objects.create(name='one hundred euros', price=eur100)
        SimpleMoneyModel.objects.create(name='one hundred and one euros', price=eur100 + 1)
        SimpleMoneyModel.objects.create(name='ninety nine euros', price=eur100 - 1)

        SimpleMoneyModel.objects.create(name='one hundred hrivnyas', price=uah100)
        SimpleMoneyModel.objects.create(name='one hundred and one hrivnyas', price=uah100 + 1)
        SimpleMoneyModel.objects.create(name='ninety nine hrivnyas', price=uah100 - 1)

        # Exact:
        qset = SimpleMoneyModel.objects.filter(price__exact=usd100)
        assert qset.count() == 1
        qset = SimpleMoneyModel.objects.filter(price__exact=eur100)
        assert qset.count() == 1
        qset = SimpleMoneyModel.objects.filter(price__exact=uah100)
        assert qset.count() == 1

        # Less than:
        qset = SimpleMoneyModel.objects.filter(price__lt=usd100)
        assert qset.count() == 1
        assert qset[0].price == usd100 - 1

        qset = SimpleMoneyModel.objects.filter(price__lt=eur100)
        assert qset.count() == 1
        assert qset[0].price == eur100 - 1

        qset = SimpleMoneyModel.objects.filter(price__lt=uah100)
        assert qset.count() == 1
        assert qset[0].price == uah100 - 1

        # Greater than:
        qset = SimpleMoneyModel.objects.filter(price__gt=usd100)
        assert qset.count() == 1
        assert qset[0].price == usd100 + 1

        qset = SimpleMoneyModel.objects.filter(price__gt=eur100)
        assert qset.count() == 1
        assert qset[0].price == eur100 + 1

        qset = SimpleMoneyModel.objects.filter(price__gt=uah100)
        assert qset.count() == 1
        assert qset[0].price == uah100 + 1

        # Less than or equal:
        qset = SimpleMoneyModel.objects.filter(price__lte=usd100)
        assert qset.count() == 2
        assertsamecurrency([ent.price for ent in qset], 'USD')
        for ent in qset:
            assert ent.price.amount <= 100

        qset = SimpleMoneyModel.objects.filter(price__lte=eur100)
        assert qset.count() == 2
        assertsamecurrency([ent.price for ent in qset], 'EUR')
        for ent in qset:
            assert ent.price.amount <= 100

        qset = SimpleMoneyModel.objects.filter(price__lte=uah100)
        assert qset.count() == 2
        assertsamecurrency([ent.price for ent in qset], 'UAH')
        for ent in qset:
            assert ent.price.amount <= 100

        # Greater than or equal:
        qset = SimpleMoneyModel.objects.filter(price__gte=usd100)
        assert qset.count() == 2
        assertsamecurrency([ent.price for ent in qset], 'USD')

        qset = SimpleMoneyModel.objects.filter(price__gte=eur100)
        assert qset.count() == 2
        assertsamecurrency([ent.price for ent in qset], 'EUR')

        qset = SimpleMoneyModel.objects.filter(price__gte=uah100)
        assert qset.count() == 2
        assertsamecurrency([ent.price for ent in qset], 'UAH')

    def test_price_attribute(self):
        m = SimpleMoneyModel()
        m.price = Money(3, 'BGN')

        assert m.price == Money(3, 'BGN')

    def test_price_attribute_in_constructor(self):
        m1 = SimpleMoneyModel(price=Money(100, 'USD'))
        m2 = SimpleMoneyModel(price=Money(200, 'JPY'))

        assert m1.price == Money(100, 'USD')
        assert m2.price == Money(200, 'JPY')

    def test_price_attribute_update(self):
        m = SimpleMoneyModel(price=Money(200, 'JPY'))
        m.price = Money(300, 'USD')
        assert m.price == Money(300, 'USD')

    def test_price_amount_to_string(self):
        m1 = SimpleMoneyModel(price=Money('200', 'JPY'))
        m2 = SimpleMoneyModel(price=Money('200.0', 'JPY'))

        assert str(m1.price) == '200 JPY'
        assert str(m1.price.amount) == '200'
        assert str(m2.price.amount) == '200.0'

    def test_price_amount_to_string_non_money(self):
        e1 = MoneyModelDefaults()

        assert str(e1.price) == '123.45 USD'
        assert str(e1.price.amount) == '123.45'

    def test_zero_edge_case(self):
        created = SimpleMoneyModel.objects.create(name='zero dollars', price=Money(0, 'USD'))
        assert created.price == Money(0, 'USD')

        ent = SimpleMoneyModel.objects.filter(price__exact=Money(0, 'USD')).get()
        assert ent.price == Money(0, 'USD')

    def test_unsupported_lookup(self):
        with pytest.raises(NotSupportedLookup):
            SimpleMoneyModel.objects.filter(price__startswith='ABC')


@pytest.mark.django_db
class TestNullability(object):
    def test_nullable_model_instance(self):
        instance = NullableMoneyModel()
        assert instance.price is None

    def test_nullable_model_save(self):
        instance = NullableMoneyModel()
        instance.save()
        assert instance.price is None

    def test_nullable_model_create_and_lookup(self):
        name = 'test_nullable_model_create_and_lookup'
        NullableMoneyModel.objects.create(name=name)
        instance = NullableMoneyModel.objects.get(name=name)
        assert instance.price is None

    def test_nullable_model_lookup_by_null_amount(self):
        name = 'test_nullable_model_lookup_by_null_amount'
        NullableMoneyModel.objects.create(name=name)

        # Assert NULL currency has 'blank' currency
        instance = NullableMoneyModel.objects.filter(price_currency='')[0]
        assert instance.name == name

    def test_nullable_model_lookup_by_null_currency(self):
        name = 'test_nullable_model_lookup_by_null_currency'
        NullableMoneyModel.objects.create(name=name)

        # Assert NULL currency has 'blank' currency
        instance = NullableMoneyModel.objects.filter(price__isnull=True)[0]
        assert instance.name == name

    def test_nullable_null_currency_vs_undefined_currency(self):
        name = 'test_nullable_null_currency_vs_undefined_currency'
        NullableMoneyModel.objects.create(name=name + '_null', price=None)
        NullableMoneyModel.objects.create(name=name + '_undefined', price=Money(0))
        assert NullableMoneyModel.objects.all().count() == 2

        # Assert NULL currency has 'blank' currency
        assert NullableMoneyModel.objects.filter(price__isnull=True).count() == 1
        null_instance = NullableMoneyModel.objects.filter(price__isnull=True)[0]
        assert null_instance.name == name + '_null'
        null_instance = NullableMoneyModel.objects.filter(price_currency='')[0]
        assert null_instance.name == name + '_null'

        assert NullableMoneyModel.objects.filter(price__isnull=False).count() == 1
        undefined_instance = NullableMoneyModel.objects.filter(price__isnull=False)[0]
        assert undefined_instance.name == name + '_undefined'
        undefined_instance = NullableMoneyModel.objects.filter(price_currency=settings.BASE_CURRENCY)[0]
        assert undefined_instance.name == name + '_undefined'


@pytest.mark.django_db
@pytest.mark.parametrize('cls', ALL_PARAMETRIZED_MODELS)
def test_manager_create(cls):
    instance = cls.objects.create()
    assert instance.value == instance.expected_value()
    assert instance.value.amount == instance.expected_value().amount
    assert instance.value.currency == instance.expected_value().currency


@pytest.mark.parametrize('cls', ALL_PARAMETRIZED_MODELS)
def test_instance_create(cls):
    instance = cls()  # should not touch the db
    assert instance.value == instance.expected_value()
    assert instance.value.amount == instance.expected_value().amount
    assert instance.value.currency == instance.expected_value().currency


@pytest.mark.django_db
@pytest.mark.parametrize('cls', ALL_PARAMETRIZED_MODELS)
def test_instance_save(cls):
    instance = cls()
    instance.save()
    assert instance.value == instance.expected_value()
    assert instance.value.amount == instance.expected_value().amount
    assert instance.value.currency == instance.expected_value().currency


@pytest.mark.django_db
@pytest.mark.parametrize('cls', ALL_PARAMETRIZED_MODELS)
def test_manager_create_override_with_money(cls):
    overridden_value = Money('9876', 'GBP')
    instance = cls.objects.create(value=overridden_value)
    assert instance.value != instance.expected_value()
    assert instance.value.amount != instance.expected_value().amount
    assert instance.value.currency != instance.expected_value().currency

    assert instance.value == overridden_value
    assert instance.value.amount == overridden_value.amount
    assert instance.value.currency == overridden_value.currency


@pytest.mark.parametrize('cls', ALL_PARAMETRIZED_MODELS)
def test_instance_create_override_with_money(cls):
    overridden_value = Money('8765', 'GBP')
    instance = cls(value=overridden_value)
    assert instance.value != instance.expected_value()
    assert instance.value.amount != instance.expected_value().amount
    assert instance.value.currency != instance.expected_value().currency

    assert instance.value == overridden_value
    assert instance.value.amount == overridden_value.amount
