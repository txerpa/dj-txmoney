# coding=utf-8
from __future__ import absolute_import, division, unicode_literals

from decimal import Decimal

import pytest

from txmoney.money.exceptions import CurrencyDoesNotExist, CurrencyMismatch, IncorrectMoneyInputError
from txmoney.money.money import CURRENCIES, Currency, Money
from txmoney.settings import txmoney_settings as settings


class TestCurrency(object):
    """
    Tests of the Currency class
    """

    CURRENCY_CREATION = [
        Currency('XXX'),
        Currency('XXX', 999),
        Currency('XXX', 999, 'Test'),
        Currency('XXX', 999, 'Test', 'X'),
        Currency('XXX', 999, 'Test', 'X', '3'),
        Currency('XXX', 999, 'Test', 'X', '3', ['España']),
    ]

    @pytest.mark.parametrize('value', CURRENCY_CREATION)
    def test_creation(self, value):
        assert isinstance(value, Currency)

    CURRENCY_EQUALITY = [
        # Equality
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) == Currency('XXX', 998, 't2', 'Y', '2', ['Japan']), True),
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) == str('XXX'), True),
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) == 'XXX', True),

        # Mismatched currencies
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) == Currency('YYY', 998, 't2', 'Y', '2', ['Japan']), False),
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) == str('YYY'), False),
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) == 'YYY', False),
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) == 12, False),

        # Inequality
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) != Currency('XXX', 998, 't2', 'Y', '2', ['Japan']), False),
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) != str('XXX'), False),
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) != 'XXX', False),

        # Mismatched currencies
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) != Currency('YYY', 998, 't2', 'Y', '2', ['Japan']), True),
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) != str('YYY'), True),
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) != 'YYY', True),
        (Currency('XXX', 999, 't1', 'X', '3', ['España']) != 12, True),
    ]

    @pytest.mark.parametrize('value,expected', CURRENCY_EQUALITY)
    def test_equality(self, value, expected):
        assert value == expected

    def test_get_by_code(self):
        assert isinstance(Currency.get_by_code('eur'), Currency)
        assert isinstance(Currency.get_by_code('EUR'), Currency)

    def test_get_by_code_error(self):
        with pytest.raises(CurrencyDoesNotExist):
            Currency.get_by_code('YYY')

    def test_all(self):
        assert isinstance(Currency.all(), dict)


class TestMoney(object):
    """
    Tests of the Money class
    """

    MONEY_CREATION = [
        # Int values
        (Money(10, 'EUR'), Decimal(10), 'EUR'),
        (Money(-10, 'EUR'), Decimal(-10), 'EUR'),
        # Str values
        (Money('10', 'EUR'), Decimal(10), 'EUR'),
        (Money('-10', 'EUR'), Decimal(-10), 'EUR'),
        (Money(str('10.50'), str('EUR')), Decimal('10.50'), 'EUR'),
        (Money(str('-10.50'), str('EUR')), Decimal('-10.50'), 'EUR'),
        (Money('10.50', 'EUR'), Decimal('10.50'), 'EUR'),
        (Money('-10.50', 'EUR'), Decimal('-10.50'), 'EUR'),
        # Float values
        (Money(10.50, 'EUR'), Decimal('10.50'), 'EUR'),
        (Money(-10.50, 'EUR'), Decimal('-10.50'), 'EUR'),
        # Decimal values
        (Money(Decimal('10.50'), 'EUR'), Decimal('10.50'), 'EUR'),
        (Money(Decimal('-10.50'), 'EUR'), Decimal('-10.50'), 'EUR'),
        # Unspecified currency
        (Money(10), Decimal(10), settings.BASE_CURRENCY),
        # Unspecified amount
        (Money(currency='EUR'), 0, 'EUR'),
        # Internal type
        (Money(1, Currency(code='AAA', name='My Currency')), 1, 'AAA'),
        # Parsed value
        (Money('10 EUR'), 10, 'EUR'),
    ]

    @pytest.mark.parametrize('value,expected_amount,expected_currency', MONEY_CREATION)
    def test_creation(self, value, expected_amount, expected_currency):
        assert isinstance(value, Money)
        assert value.amount == expected_amount
        assert value.currency.code == expected_currency

    MONEY_CREATION_UNSUPPORTED = [
        (lambda: Money('10 EUR', 'USD')),
        (lambda: Money('EUR 10 EUR')),
    ]

    @pytest.mark.parametrize('value', MONEY_CREATION_UNSUPPORTED)
    def test_invalid_creation(self, value):
        with pytest.raises(IncorrectMoneyInputError):
            value()

    def test_amount_attribute(self):
        value = Money(101, 'USD')
        assert value.amount == 101

    def test_mutation_of_amount_attribute(self):
        money = Money('2', 'EUR')
        with pytest.raises(AttributeError):
            money.amount = 1

    MONEY_PRECISION = [
        (Money('10 EUR'), Decimal(10)),
        (Money('10.2 EUR'), Decimal('10.2')),
        (Money('10.225 EUR'), Decimal('10.23')),
        (Money('10.226 EUR'), Decimal('10.23')),
        (Money('10.2288 EUR'), Decimal('10.23'))
    ]

    @pytest.mark.parametrize('value,expected', MONEY_PRECISION)
    def test_amount_rounded_attribute(self, value, expected):
        assert value.amount_rounded == expected

    def test_mutation_of_amount_rounded_attribute(self):
        money = Money('2', 'EUR')
        with pytest.raises(AttributeError):
            money.amount_rounded = 1

    def test_currency_attribute(self):
        value = Money(101, 'USD')
        assert value.currency == 'USD'

    def test_mutation_of_currency_attribute(self):
        money = Money('2', 'EUR')
        with pytest.raises(AttributeError):
            money.currency = 'USD'

    MONEY_STRINGS = [
        # Default currency:
        (Money(' 123'), '123 {}'.format(settings.BASE_CURRENCY),),
        (Money('-123'), '-123 {}'.format(settings.BASE_CURRENCY),),
        # Test a currency with decimals:
        (Money('123', 'EUR'), '123 EUR',),
        (Money('-123', 'EUR'), '-123 EUR',),
        (Money('123.0000', 'EUR'), '123.0000 EUR',),
        (Money('-123.0000', 'EUR'), '-123.0000 EUR',),
        (Money('123.25', 'EUR'), '123.25 EUR',),
        (Money('-123.25', 'EUR'), '-123.25 EUR',),
        # Test a currency that is normally written without decimals:
        (Money('123', 'JPY'), '123 JPY',),
        (Money('-123', 'JPY'), '-123 JPY',),
        (Money('123.0000', 'JPY'), '123.0000 JPY',),
        (Money('-123.0000', 'JPY'), '-123.0000 JPY',),
        (Money('123.25', 'JPY'), '123.25 JPY',),
        (Money('-123.25', 'JPY'), '-123.25 JPY',),
    ]

    @pytest.mark.parametrize('value,expected', MONEY_STRINGS)
    def test_str(self, value, expected):
        assert str(value) == expected

    @pytest.mark.parametrize('value,expected', MONEY_STRINGS)
    def test_repr(self, value, expected):
        assert repr(value) == expected

    MONEY_ARITHMETIC = [
        # Casting
        (lambda: Money('100') + 0.5, Money('100.5')),
        (lambda: float(Money('100')), float(100)),
        (lambda: int(Money('100')), 100),

        # Addition
        (lambda: Money('100') + Money('100'), Money('200')),
        (lambda: Money('100') + Money('-100'), Money('0')),
        (lambda: Money('100') + 100, Money('200')),
        (lambda: Money('100') + -100, Money('0')),
        (lambda: Money('100') + Decimal('100'), Money('200')),
        (lambda: Money('100') + Decimal('-100'), Money('0')),

        # Subtraction
        (lambda: Money('100') - Money('100'), Money('0')),
        (lambda: Money('100') - Money('-100'), Money('200')),
        (lambda: Money('100') - 100, Money('0')),
        (lambda: Money('100') - -100, Money('200')),
        (lambda: Money('100') - Decimal('100'), Money('0')),
        (lambda: Money('100') - Decimal('-100'), Money('200')),

        # Multiplication
        (lambda: Money('100') * 4, Money('400')),
        (lambda: Money('100') * Decimal('4'), Money('400')),

        # Division
        (lambda: Money('100') / 4, Money('25')),
        (lambda: Money('100') / Decimal('4'), Money('25')),

        # Negation
        (lambda: - Money('100'), Money('-100')),
        (lambda: - Money('100.12', 'EUR'), Money('-100.12', 'EUR')),
        (lambda: + Money('100'), Money('100')),

        # Absolute value
        (lambda: abs(Money('-100')), Money('100')),
        (lambda: abs(Money('-100.12', 'EUR')), Money('100.12', 'EUR')),
        (lambda: abs(Money('0')), Money('0')),
        (lambda: abs(Money('100')), Money('100')),
        (lambda: abs(Money('100.12', 'EUR')), Money('100.12', 'EUR')),
    ]

    @pytest.mark.parametrize('value,expected', MONEY_ARITHMETIC)
    def test_arithmetic(self, value, expected):
        result = value()
        assert result == expected

    MONEY_ARITHMETIC_UNSUPPORTED = [
        # Modulus
        (lambda: 4 % Money('100')),
        (lambda: Decimal('4') % Money('100')),
        (lambda: Money('100') % 4),
        (lambda: Money('100') % Decimal('4')),

        # Division: floor division (see future import above)
        (lambda: Money('100') // 4),
        (lambda: Money('100') // Decimal('4')),

        # Dividing a value by Money
        (lambda: 4 / Money('100')),
        (lambda: Decimal('4') / Money('100')),
        (lambda: Money('100') / Money('100')),

        # Multiplication of 2 Money objects
        (lambda: Money('100') * Money('100')),

        # Subtracting money from a digit
        (lambda: 100 - Money('100')),
        (lambda: -100 - Money('100')),
        (lambda: Decimal('100') - Money('100')),
        (lambda: Decimal('-100') - Money('100')),
    ]

    @pytest.mark.parametrize('value', MONEY_ARITHMETIC_UNSUPPORTED)
    def test_invalid_arithmetic(self, value):
        with pytest.raises(TypeError):
            value()

    MONEY_ARITHMETIC_MISMATCHED = [
        # Mismatched currencies
        (lambda: Money('100', 'JPY') + Money('100', 'EUR')),
        (lambda: Money('100', 'JPY') - Money('100', 'EUR')),
    ]

    @pytest.mark.parametrize('value', MONEY_ARITHMETIC_MISMATCHED)
    def test_invalid_currency(self, value):
        with pytest.raises(CurrencyMismatch):
            value()

    MONEY_EQUALITY = [
        # Bool
        (bool(Money('0')), False),
        (bool(Money('1')), True),
        (bool(Money('0', 'EUR')), False),
        (bool(Money('1', 'EUR')), True),
        (bool(Money('-1', 'EUR')), True),

        # Equality
        (Money('0') == Money('0'), True),
        (Money('100') == Money('100'), True),
        (Money('-100') == Money('-100'), True),
        (Money('100', 'EUR') == Money('100', 'EUR'), True),
        (Money('100.0', 'EUR') == Money('100', 'EUR'), True),

        # Mismatched currencies
        (Money('0', 'EUR') == Money('0', 'JPY'), False),
        (Money('100', 'JPY') == Money('100'), False),
        (Money('100', 'EUR') == Money('100', 'JPY'), False),
        (Money('100.0', 'EUR') == Money('100', 'JPY'), False),

        # Other types
        (Money('100.0', 'EUR') == Decimal('100'), False),
        (Money('100.0', 'EUR') == 100, False),
        (Decimal('100') == Money('100.0', 'EUR'), False),
        (100 == Money('100.0', 'EUR'), False),

        # Inequality
        (Money('0') != Money('0'), False),
        (Money('100') != Money('100'), False),
        (Money('-100') != Money('-100'), False),
        (Money('100', 'EUR') != Money('100', 'EUR'), False),
        (Money('100.0', 'EUR') != Money('100', 'EUR'), False),

        # Mismatched currencies
        (Money('0', 'EUR') != Money('0', 'JPY'), True),
        (Money('100', 'JPY') != Money('100'), True),
        (Money('100', 'EUR') != Money('100', 'JPY'), True),
        (Money('100.0', 'EUR') != Money('100', 'JPY'), True),

        # Other types
        (Money('100.0', 'EUR') != Decimal('100'), True),
        (Money('100.0', 'EUR') != 100, True),
        (Decimal('100') != Money('100.0', 'EUR'), True),
        (100 != Money('100.0', 'EUR'), True),

        # LT/GT
        (0 < Money('0'), False),
        (100 < Money('100'), False),
        (-100 < Money('-100'), False),
        (100 < Money('100', 'EUR'), False),
        (100.0 < Money('100', 'EUR'), False),

        (0 > Money('1'), False),
        (1 > Money('0'), True),
        (-101 > Money('-100'), False),
        (-100 > Money('-101'), True),
        (100 > Money('100.01', 'EUR'), False),
        (100.01 > Money('100', 'EUR'), True),

        (Money('0') < Money('0'), False),
        (Money('100') < Money('100'), False),
        (Money('-100') < Money('-100'), False),
        (Money('100', 'EUR') < Money('100', 'EUR'), False),
        (Money('100.0', 'EUR') < Money('100', 'EUR'), False),

        (Money('0') > Money('0'), False),
        (Money('100') > Money('100'), False),
        (Money('-100') > Money('-100'), False),
        (Money('100', 'EUR') > Money('100', 'EUR'), False),

        (Money('0') < Money('1'), True),
        (Money('1') < Money('0'), False),
        (Money('-101') < Money('-100'), True),
        (Money('-100') < Money('-101'), False),
        (Money('100', 'EUR') < Money('100.01', 'EUR'), True),
        (Money('100.01', 'EUR') < Money('100', 'EUR'), False),

        (Money('0') > Money('1'), False),
        (Money('1') > Money('0'), True),
        (Money('-101') > Money('-100'), False),
        (Money('-100') > Money('-101'), True),
        (Money('100', 'EUR') > Money('100.01', 'EUR'), False),
        (Money('100.01', 'EUR') > Money('100', 'EUR'), True),

        (Money('100.0', 'EUR') < Money('100', 'EUR'), False),
        (Money('100.0', 'EUR') > Money('100', 'EUR'), False),

        # GTE/LTE
        (Money('0') <= Money('0'), True),
        (Money('100') <= Money('100'), True),
        (Money('-100') <= Money('-100'), True),
        (Money('100', 'EUR') <= Money('100', 'EUR'), True),
        (Money('100.0', 'EUR') <= Money('100', 'EUR'), True),

        (Money('0') >= Money('0'), True),
        (Money('100') >= Money('100'), True),
        (Money('-100') >= Money('-100'), True),
        (Money('100', 'EUR') >= Money('100', 'EUR'), True),
        (Money('100.0', 'EUR') >= Money('100', 'EUR'), True),

        (Money('0') <= Money('1'), True),
        (Money('1') <= Money('0'), False),
        (Money('-101') <= Money('-100'), True),
        (Money('-100') <= Money('-101'), False),
        (Money('100', 'EUR') <= Money('100.01', 'EUR'), True),
        (Money('100.01', 'EUR') <= Money('100', 'EUR'), False),

        (Money('0') >= Money('1'), False),
        (Money('1') >= Money('0'), True),
        (Money('-101') >= Money('-100'), False),
        (Money('-100') >= Money('-101'), True),
        (Money('100', 'EUR') >= Money('100.01', 'EUR'), False),
        (Money('100.01', 'EUR') >= Money('100', 'EUR'), True),

        (Money('100.0', 'EUR') <= Money('100', 'EUR'), True),
        (Money('100.0', 'EUR') >= Money('100', 'EUR'), True),
    ]

    @pytest.mark.parametrize('value,expected', MONEY_EQUALITY)
    def test_equality(self, value, expected):
        assert value == expected

    def test_string_parse(self):
        value = Money.from_string('100.0 GBP')
        assert value.amount == Decimal('100.0')
        assert value.currency == 'GBP'
        assert value.currency == CURRENCIES['GBP']

    def test_string_parse_default_currency(self):
        value = Money.from_string('100.35')
        assert value.amount == Decimal('100.35')
        assert value.currency == settings.BASE_CURRENCY
        assert value.currency == CURRENCIES[settings.BASE_CURRENCY]

    MONEY_ROUND = [
        (lambda: Money('123.001', 'EUR').round(), Money('123', 'EUR')),
        (lambda: Money('123.005', 'EUR').round(), Money('123.01', 'EUR')),
        (lambda: Money('123.006', 'EUR').round(), Money('123.01', 'EUR')),
        (lambda: Money('123.001', 'EUR').round(3), Money('123.001', 'EUR')),
        (lambda: Money('123.005', 'EUR').round(3), Money('123.005', 'EUR')),
        (lambda: Money('123.006', 'EUR').round(3), Money('123.006', 'EUR')),
    ]

    @pytest.mark.parametrize('value,expected', MONEY_ROUND)
    def test_round(self, value, expected):
        assert value() == expected
