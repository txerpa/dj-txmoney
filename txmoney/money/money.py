# coding=utf-8
from __future__ import absolute_import, division, unicode_literals

from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from six import python_2_unicode_compatible, string_types

from ..rates.models import Rate
from ..settings import txmoney_settings as settings
from .exceptions import CurrencyDoesNotExist, CurrencyMismatch, IncorrectMoneyInputError, InvalidMoneyOperation


CURRENCIES = {}


class Currency(object):
    """
    A Currency represents a form of money issued by governments, and
    used in one or more states/countries. A Currency instance
    encapsulates the related data of: the ISO 4217 currency/numeric code, a
    canonical name, the currency symbol, used decimals and countries the currency is used in.
    """

    def __init__(self, code, numeric='', name='', symbol='', decimals=2, countries=None):
        """
        :param code: (Unicode) ISO 4217 currency code
        :param numeric: (Integer) ISO 4217 currency number
        :param name: (Unicode) currency name
        :param symbol: (Unicode) currency symbol
        :param decimals: (Integer) currency decimals
        :param countries: (Unicode list) countries which currency is main currency
        """
        if not countries:
            countries = []
        self.code = code
        self.numeric = numeric
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
        self.countries = countries

    def __repr__(self):
        return self.code

    def __eq__(self, other):
        if isinstance(other, Currency):
            return self.code and other.code and self.code == other.code
        if isinstance(other, string_types):
            return self.code == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def get_by_code(code):
        """
        Search a currency by its code.
        :param code: (String) ISO 4217 currency code
        :return: (Currency) currency
        """
        try:
            return CURRENCIES[str(code).upper()]
        except KeyError:
            raise CurrencyDoesNotExist(code)

    @staticmethod
    def all():
        """
        Get all currencies which system allows.
        :return: (Dictionary) Currencies
        """
        return CURRENCIES


@python_2_unicode_compatible
class Money(object):
    """
    A Money instance is a combination of data - an amount and a
    optional currency - along with operators that handle the semantics of money
    operations in a better way than just dealing with raw Decimal or floats.

    The following are supported:
        Money()                 # 0 XXX
        Money(123)              # 123 XXX
        Money(123.00)           # 123.00 XXX
        Money('123.00')         # 123.00 XXX
        Money('123', 'EUR')     # 123 EUR
        Money('123.00', 'EUR')  # 123.00 EUR

        # Parsed string
        Money('123.00 EUR')     # 123.00 EUR

        # Decimal
        Money(Decimal('123.0'), 'USD')   # 123.0 USD

        # kwargs
        Money(amount='123.0', currency='USD')   # 123.0 USD

        # native types
        Money(Decimal('123.0'), Currency(code='AAA', name='My Currency')  # 123.0 AAA
    """

    def __init__(self, amount=0, currency=None):
        if isinstance(amount, Decimal):
            if amount in (Decimal('Inf'), Decimal('-Inf')):
                raise IncorrectMoneyInputError(
                    'Cannot initialize with infinity amount'.format(currency, amount)
                )
            self._amount = amount
        else:
            try:
                self._amount = Decimal(smart_text(amount).strip())
            except InvalidOperation:
                try:
                    # check for the odd case of Money("123.00 EUR", "USD")
                    if currency:
                        raise IncorrectMoneyInputError(
                            'Initialized with conflicting currencies {} {}'.format(currency, amount)
                        )

                    self._amount, currency = self._from_string(amount)
                except:
                    raise IncorrectMoneyInputError('Cannot initialize with amount {}'.format(amount))

        if not currency:
            currency = settings.BASE_CURRENCY

        if not isinstance(currency, Currency):
            currency = Currency.get_by_code(currency)

        self._currency = currency
        assert isinstance(self._amount, Decimal)
        assert isinstance(self._currency, Currency)

    @property
    def amount(self):
        """
        Amount in decimal full precision
        :return: deciamal
        """
        return self._amount

    @property
    def amount_rounded(self):
        """
        Amount in decimal currency precision
        :return:
        """
        decimals = Decimal(10) ** -self._currency.decimals
        return self._amount.quantize(decimals, rounding=ROUND_HALF_UP)

    @property
    def currency(self):
        return self._currency

    @classmethod
    def _from_string(cls, value):
        s = str(value).strip()
        try:
            amount = Decimal(s)
            currency = settings.BASE_CURRENCY
        except InvalidOperation:
            try:
                amount = Decimal(s[:len(s) - 3].strip())
                currency = Currency.get_by_code(s[len(s) - 3:])
            except:
                raise IncorrectMoneyInputError('The value "{}" is not properly formatted as "123.45 XXX"'.format(s))
        return amount, currency

    @classmethod
    def from_string(cls, value):
        """
        Parses a properly formatted string. The string should be formatted as
        given by the repr function: '123.45 EUR'
        """
        return Money(*cls._from_string(value))

    def _currency_check(self, other):
        """ Compare the currencies matches and raise if not """
        if self._currency != other.currency:
            raise CurrencyMismatch('Currency mismatch: {} != {}'.format(self._currency, other.currency))

    def __str__(self):
        return '{} {}'.format(self._amount, self._currency)

    def __repr__(self):
        return str(self)

    def __float__(self):
        return float(self._amount)

    def __int__(self):
        return int(self._amount)

    def __pos__(self):
        return Money(amount=self._amount, currency=self._currency)

    def __neg__(self):
        return self.__class__(-self._amount, self._currency)

    def __abs__(self):
        return Money(amount=abs(self._amount), currency=self._currency)

    def __add__(self, other):
        if isinstance(other, Money):
            self._currency_check(other)
            return Money(amount=self._amount + other.amount, currency=self._currency)
        else:
            return Money(amount=self._amount + Decimal(str(other)), currency=self._currency)

    def __sub__(self, other):
        if isinstance(other, Money):
            self._currency_check(other)
            return Money(amount=self._amount - other.amount, currency=self._currency)
        else:
            return Money(amount=self._amount - Decimal(str(other)), currency=self._currency)

    def __rsub__(self, other):
        # In the case where both values are Money, the left hand one will be
        # called. In the case where we are subtracting Money from another
        # value, we want to disallow it
        raise TypeError('Cannot subtract Money from {}'.format(other))

    def __mul__(self, other):
        if isinstance(other, Money):
            raise InvalidMoneyOperation('Cannot multiply monetary quantities')
        return Money(amount=self._amount * Decimal(str(other)), currency=self._currency)

    def __truediv__(self, other):
        """
        We allow division by non-money numeric values but dividing by
        another Money value is undefined
        """
        if isinstance(other, Money):
            raise InvalidMoneyOperation('Cannot divide two monetary quantities')
        return Money(amount=self._amount / other, currency=self._currency)

    __div__ = __truediv__

    def __floordiv__(self, other):
        raise InvalidMoneyOperation('Floor division not supported for monetary quantities')

    def __rtruediv__(self, other):
        raise InvalidMoneyOperation('Cannot divide by monetary quantities')

    __rdiv__ = __rtruediv__

    # Commutative operations
    __radd__ = __add__
    __rmul__ = __mul__

    # Boolean
    def __bool__(self):
        return self._amount != 0

    __nonzero__ = __bool__

    # Comparison operators
    def __eq__(self, other):
        if isinstance(other, Money):
            return (self._amount == other.amount) and (self._currency == other.currency)
        # Allow comparison to 0
        if (other == 0) and (self._amount == 0):
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, Money):
            self._currency_check(other)
            return self._amount < other.amount
        else:
            return self._amount < Decimal(str(other))

    def __gt__(self, other):
        if isinstance(other, Money):
            self._currency_check(other)
            return self._amount > other.amount
        else:
            return self._amount > Decimal(str(other))

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def round(self, n=None):
        n = n or self._currency.decimals
        decimals = Decimal(10) ** -n
        return self.__class__(self._amount.quantize(decimals, rounding=ROUND_HALF_UP), self._currency)

    def allocate(self, ratios):
        """
        Allocates a sum of money
        :param ratios: allocation ratios
        :return: Money list of allocated money
        """
        total = sum(ratios)
        remainder = self._amount
        results = []

        for i in range(0, len(ratios)):
            results.append(Money(self._amount * ratios[i] / total, self._currency))
            remainder -= results[i].amount

        results[-1] = Money(results[-1].amount + remainder, self._currency)

        return results

    def exchange_to(self, currency=settings.BASE_CURRENCY, rate_date=date.today()):
        """
        Exchange money object to given currency for a date
        :param currency: destination currency. Must be Currency object or ISO 4217 string
        :param rate_date: rate date
        :param rate_date: rate date
        :return: Money object
        """

        # If same currency not exchange
        if self._currency == currency:
            return self

        # Get currency for string
        if not isinstance(currency, Currency):
            currency = Currency.get_by_code(currency)

        amount = self._amount / Rate.get_ratio(self._currency, currency, rate_date)

        return self.__class__(amount, currency)


# Definitions of ISO 4217 Currencies
# Source: http://www.xe.com/iso4217.php
# Symbols: http://www.xe.com/symbols.php

CURRENCIES['AED'] = Currency(code='AED', numeric='784', decimals=2, symbol='د.إ',
                             name=_('UAE Dirham'),
                             countries=['UNITED ARAB EMIRATES'])
CURRENCIES['AFN'] = Currency(code='AFN', numeric='971', decimals=2, symbol='؋',
                             name=_('Afghani'),
                             countries=['AFGHANISTAN'])
CURRENCIES['ALL'] = Currency(code='ALL', numeric='008', decimals=2, symbol='Lek', name=_('Lek'),
                             countries=['ALBANIA'])
CURRENCIES['AMD'] = Currency(code='AMD', numeric='051', decimals=2, symbol='֏',
                             name=_('Armenian Dram'),
                             countries=['ARMENIA'])
CURRENCIES['ANG'] = Currency(code='ANG', numeric='532', decimals=2, symbol='ƒ',
                             name=_('Netherlands Antillean Guilder'),
                             countries=['CURA\xc7AO', 'SINT MAARTEN (DUTCH PART)'])
CURRENCIES['AOA'] = Currency(code='AOA', numeric='973', decimals=2, symbol='', name=_('Kwanza'),
                             countries=['ANGOLA'])
CURRENCIES['ARS'] = Currency(code='ARS', numeric='032', decimals=2, symbol='$',
                             name=_('Argentine Peso'),
                             countries=['ARGENTINA'])
CURRENCIES['AUD'] = Currency(code='AUD', numeric='036', decimals=2, symbol='$',
                             name=_('Australian Dollar'),
                             countries=['AUSTRALIA', 'CHRISTMAS ISLAND',
                                        'COCOS (KEELING) ISLANDS',
                                        'HEARD ISLAND AND McDONALD ISLANDS', 'KIRIBATI',
                                        'NAUR', 'NORFOLK ISLAND',
                                        'TUVAL'])
CURRENCIES['AWG'] = Currency(code='AWG', numeric='533', decimals=2, symbol='ƒ',
                             name=_('Aruban Florin'),
                             countries=['ARUBA'])
CURRENCIES['AZN'] = Currency(code='AZN', numeric='944', decimals=2, symbol='ман',
                             name=_('Azerbaijanian Manat'),
                             countries=['AZERBAIJAN'])
CURRENCIES['BAM'] = Currency(code='BAM', numeric='977', decimals=2, symbol='KM',
                             name=_('Convertible Mark'),
                             countries=['BOSNIA AND HERZEGOVINA'])
CURRENCIES['BBD'] = Currency(code='BBD', numeric='052', decimals=2, symbol='$',
                             name=_('Barbados Dollar'),
                             countries=['BARBADOS'])
CURRENCIES['BDT'] = Currency(code='BDT', numeric='050', decimals=2, symbol='৳', name=_('Taka'),
                             countries=['BANGLADESH'])
CURRENCIES['BGN'] = Currency(code='BGN', numeric='975', decimals=2, symbol='лв',
                             name=_('Bulgarian Lev'),
                             countries=['BULGARIA'])
CURRENCIES['BHD'] = Currency(code='BHD', numeric='048', decimals=3, symbol='',
                             name=_('Bahraini Dinar'),
                             countries=['BAHRAIN'])
CURRENCIES['BIF'] = Currency(code='BIF', numeric='108', decimals=0, symbol='',
                             name=_('Burundi Franc'),
                             countries=['BURUNDI'])
CURRENCIES['BMD'] = Currency(code='BMD', numeric='060', decimals=2, symbol='$',
                             name=_('Bermudian Dollar'),
                             countries=['BERMUDA'])
CURRENCIES['BND'] = Currency(code='BND', numeric='096', decimals=2, symbol='$',
                             name=_('Brunei Dollar'),
                             countries=['BRUNEI DARUSSALAM'])
CURRENCIES['BOB'] = Currency(code='BOB', numeric='068', decimals=2, symbol='$b',
                             name=_('Boliviano'),
                             countries=['BOLIVIA, PLURINATIONAL STATE OF'])
CURRENCIES['BRL'] = Currency(code='BRL', numeric='986', decimals=2, symbol='R$',
                             name=_('Brazilian Real'),
                             countries=['BRAZIL'])
CURRENCIES['BSD'] = Currency(code='BSD', numeric='044', decimals=2, symbol='$',
                             name=_('Bahamian Dollar'),
                             countries=['BAHAMAS'])
CURRENCIES['BTN'] = Currency(code='BTN', numeric='064', decimals=2, symbol='',
                             name=_('Ngultrum'),
                             countries=['BHUTAN'])
CURRENCIES['BWP'] = Currency(code='BWP', numeric='072', decimals=2, symbol='P', name=_('Pula'),
                             countries=['BOTSWANA'])
CURRENCIES['BYR'] = Currency(code='BYR', numeric='974', decimals=0, symbol='p.',
                             name=_('Belarussian Ruble'),
                             countries=['BELARUS'])
CURRENCIES['BZD'] = Currency(code='BZD', numeric='084', decimals=2, symbol='BZ$',
                             name=_('Belize Dollar'),
                             countries=['BELIZE'])
CURRENCIES['CAD'] = Currency(code='CAD', numeric='124', decimals=2, symbol='$',
                             name=_('Canadian Dollar'),
                             countries=['CANADA'])
CURRENCIES['CDF'] = Currency(code='CDF', numeric='976', decimals=2, symbol='',
                             name=_('Congolese Franc'),
                             countries=['CONGO, THE DEMOCRATIC REPUBLIC OF'])
CURRENCIES['CHF'] = Currency(code='CHF', numeric='756', decimals=2, symbol='Fr.',
                             name=_('Swiss Franc'),
                             countries=['LIECHTENSTEIN', 'SWITZERLAND'])
CURRENCIES['CLP'] = Currency(code='CLP', numeric='152', decimals=0, symbol='$',
                             name=_('Chilean Peso'),
                             countries=['CHILE'])
CURRENCIES['CNY'] = Currency(code='CNY', numeric='156', decimals=2, symbol='¥',
                             name=_('Yuan Renminbi'),
                             countries=['CHINA'])
CURRENCIES['COP'] = Currency(code='COP', numeric='170', decimals=2, symbol='$',
                             name=_('Colombian Peso'),
                             countries=['COLOMBIA'])
CURRENCIES['CRC'] = Currency(code='CRC', numeric='188', decimals=2, symbol='₡',
                             name=_('Costa Rican Colon'),
                             countries=['COSTA RICA'])
CURRENCIES['CUC'] = Currency(code='CUC', numeric='931', decimals=2, symbol='',
                             name=_('Peso Convertible'),
                             countries=['CUBA'])
CURRENCIES['CUP'] = Currency(code='CUP', numeric='192', decimals=2, symbol='₱',
                             name=_('Cuban Peso'),
                             countries=['CUBA'])
CURRENCIES['CVE'] = Currency(code='CVE', numeric='132', decimals=2, symbol='',
                             name=_('Cape Verde Escudo'),
                             countries=['CAPE VERDE'])
CURRENCIES['CZK'] = Currency(code='CZK', numeric='203', decimals=2, symbol='Kč',
                             name=_('Czech Koruna'),
                             countries=['CZECH REPUBLIC'])
CURRENCIES['DJF'] = Currency(code='DJF', numeric='262', decimals=0, symbol='',
                             name=_('Djibouti Franc'),
                             countries=['DJIBOUTI'])
CURRENCIES['DKK'] = Currency(code='DKK', numeric='208', decimals=2, symbol='kr',
                             name=_('Danish Krone'),
                             countries=['DENMARK', 'FAROE ISLANDS', 'GREENLAND'])
CURRENCIES['DOP'] = Currency(code='DOP', numeric='214', decimals=2, symbol='RD$',
                             name=_('Dominican Peso'),
                             countries=['DOMINICAN REPUBLIC'])
CURRENCIES['DZD'] = Currency(code='DZD', numeric='012', decimals=2, symbol='',
                             name=_('Algerian Dinar'),
                             countries=['ALGERIA'])
CURRENCIES['EGP'] = Currency(code='EGP', numeric='818', decimals=2, symbol='£',
                             name=_('Egyptian Pound'),
                             countries=['EGYPT'])
CURRENCIES['ERN'] = Currency(code='ERN', numeric='232', decimals=2, symbol='', name=_('Nakfa'),
                             countries=['ERITREA'])
CURRENCIES['ETB'] = Currency(code='ETB', numeric='230', decimals=2, symbol='',
                             name=_('Ethiopian Birr'),
                             countries=['ETHIOPIA'])
CURRENCIES['EUR'] = Currency(code='EUR', numeric='978', decimals=2, symbol='€', name=_('Euro'),
                             countries=['ÅLAND ISLANDS', 'ANDORRA', 'AUSTRIA', 'BELGIUM',
                                        'CYPRUS', 'ESTONIA',
                                        'EUROPEAN UNION ', 'FINLAND', 'FRANCE',
                                        'FRENCH GUIANA',
                                        'FRENCH SOUTHERN TERRITORIES', 'GERMANY', 'GREECE',
                                        'GUADELOUPE',
                                        'HOLY SEE (VATICAN CITY STATE)', 'IRELAND', 'ITALY',
                                        'LATVIA', 'LITHUANIA',
                                        'LUXEMBOURG', 'MALTA', 'MARTINIQUE', 'MAYOTTE',
                                        'MONACO', 'MONTENEGRO',
                                        'NETHERLANDS', 'PORTUGAL', 'R\xc9UNION',
                                        'SAINT BARTH\xc9LEMY',
                                        'SAINT MARTIN (FRENCH PART)',
                                        'SAINT PIERRE AND MIQUELON', 'SAN MARINO',
                                        'SLOVAKIA', 'SLOVENIA', 'SPAIN',
                                        'Vatican City State (HOLY SEE)'])
CURRENCIES['FJD'] = Currency(code='FJD', numeric='242', decimals=2, symbol='$',
                             name=_('Fiji Dollar'),
                             countries=['FIJI'])
CURRENCIES['FKP'] = Currency(code='FKP', numeric='238', decimals=2, symbol='£',
                             name=_('Falkland Islands Pound'),
                             countries=['FALKLAND ISLANDS (MALVINAS)'])
CURRENCIES['GBP'] = Currency(code='GBP', numeric='826', decimals=2, symbol='£',
                             name=_('Pound Sterling'),
                             countries=['GUERNSEY', 'ISLE OF MAN', 'JERSEY', 'UNITED KINGDOM'])
CURRENCIES['GEL'] = Currency(code='GEL', numeric='981', decimals=2, symbol='', name=_('Lari'),
                             countries=['GEORGIA'])
CURRENCIES['GHS'] = Currency(code='GHS', numeric='936', decimals=2, symbol='',
                             name=_('Ghana Cedi'),
                             countries=['GHANA'])
CURRENCIES['GIP'] = Currency(code='GIP', numeric='292', decimals=2, symbol='£',
                             name=_('Gibraltar Pound'),
                             countries=['GIBRALTAR'])
CURRENCIES['GMD'] = Currency(code='GMD', numeric='270', decimals=2, symbol='', name=_('Dalasi'),
                             countries=['GAMBIA'])
CURRENCIES['GNF'] = Currency(code='GNF', numeric='324', decimals=0, symbol='',
                             name=_('Guinea Franc'),
                             countries=['GUINEA'])
CURRENCIES['GTQ'] = Currency(code='GTQ', numeric='320', decimals=2, symbol='Q',
                             name=_('Quetzal'),
                             countries=['GUATEMALA'])
CURRENCIES['GYD'] = Currency(code='GYD', numeric='328', decimals=2, symbol='$',
                             name=_('Guyana Dollar'),
                             countries=['GUYANA'])
CURRENCIES['HKD'] = Currency(code='HKD', numeric='344', decimals=2, symbol='HK$',
                             name=_('Hong Kong Dollar'),
                             countries=['HONG KONG'])
CURRENCIES['HNL'] = Currency(code='HNL', numeric='340', decimals=2, symbol='L',
                             name=_('Lempira'),
                             countries=['HONDURAS'])
CURRENCIES['HRK'] = Currency(code='HRK', numeric='191', decimals=2, symbol='kn',
                             name=_('Croatian Kuna'),
                             countries=['CROATIA'])
CURRENCIES['HTG'] = Currency(code='HTG', numeric='332', decimals=2, symbol='', name=_('Gourde'),
                             countries=['HAITI'])
CURRENCIES['HUF'] = Currency(code='HUF', numeric='348', decimals=2, symbol='Ft',
                             name=_('Forint'),
                             countries=['HUNGARY'])
CURRENCIES['IDR'] = Currency(code='IDR', numeric='360', decimals=2, symbol='Rp',
                             name=_('Rupiah'),
                             countries=['INDONESIA'])
CURRENCIES['ILS'] = Currency(code='ILS', numeric='376', decimals=2, symbol='₪',
                             name=_('New Israeli Sheqel'),
                             countries=['ISRAEL'])
CURRENCIES['INR'] = Currency(code='INR', numeric='356', decimals=2, symbol='',
                             name=_('Indian Rupee'),
                             countries=['BHUTAN', 'INDIA'])
CURRENCIES['IQD'] = Currency(code='IQD', numeric='368', decimals=3, symbol='',
                             name=_('Iraqi Dinar'),
                             countries=['IRAQ'])
CURRENCIES['IRR'] = Currency(code='IRR', numeric='364', decimals=2, symbol='﷼',
                             name=_('Iranian Rial'),
                             countries=['IRAN, ISLAMIC REPUBLIC OF'])
CURRENCIES['ISK'] = Currency(code='ISK', numeric='352', decimals=0, symbol='kr',
                             name=_('Iceland Krona'),
                             countries=['ICELAND'])
CURRENCIES['JMD'] = Currency(code='JMD', numeric='388', decimals=2, symbol='J$',
                             name=_('Jamaican Dollar'),
                             countries=['JAMAICA'])
CURRENCIES['JOD'] = Currency(code='JOD', numeric='400', decimals=3, symbol='',
                             name=_('Jordanian Dinar'),
                             countries=['JORDAN'])
CURRENCIES['JPY'] = Currency(code='JPY', numeric='392', decimals=0, symbol='¥', name=_('Yen'),
                             countries=['JAPAN'])
CURRENCIES['KES'] = Currency(code='KES', numeric='404', decimals=2, symbol='',
                             name=_('Kenyan Shilling'),
                             countries=['KENYA'])
CURRENCIES['KGS'] = Currency(code='KGS', numeric='417', decimals=2, symbol='лв', name=_('Som'),
                             countries=['KYRGYZSTAN'])
CURRENCIES['KHR'] = Currency(code='KHR', numeric='116', decimals=2, symbol='៛', name=_('Riel'),
                             countries=['CAMBODIA'])
CURRENCIES['KMF'] = Currency(code='KMF', numeric='174', decimals=0, symbol='',
                             name=_('Comoro Franc'),
                             countries=['COMOROS'])
CURRENCIES['KPW'] = Currency(code='KPW', numeric='408', decimals=2, symbol='₩',
                             name=_('North Korean Won'),
                             countries=['KOREA, DEMOCRATIC PEOPLE\u2019S REPUBLIC OF'])
CURRENCIES['KRW'] = Currency(code='KRW', numeric='410', decimals=0, symbol='₩', name=_('Won'),
                             countries=['KOREA, REPUBLIC OF'])
CURRENCIES['KWD'] = Currency(code='KWD', numeric='414', decimals=3, symbol='',
                             name=_('Kuwaiti Dinar'),
                             countries=['KUWAIT'])
CURRENCIES['KYD'] = Currency(code='KYD', numeric='136', decimals=2, symbol='$',
                             name=_('Cayman Islands Dollar'),
                             countries=['CAYMAN ISLANDS'])
CURRENCIES['KZT'] = Currency(code='KZT', numeric='398', decimals=2, symbol='лв',
                             name=_('Tenge'),
                             countries=['KAZAKHSTAN'])
CURRENCIES['LAK'] = Currency(code='LAK', numeric='418', decimals=2, symbol='₭', name=_('Kip'),
                             countries=['LAO PEOPLE\u2019S DEMOCRATIC REPUBLIC'])
CURRENCIES['LBP'] = Currency(code='LBP', numeric='422', decimals=2, symbol='£',
                             name=_('Lebanese Pound'),
                             countries=['LEBANON'])
CURRENCIES['LKR'] = Currency(code='LKR', numeric='144', decimals=2, symbol='₨',
                             name=_('Sri Lanka Rupee'),
                             countries=['SRI LANKA'])
CURRENCIES['LRD'] = Currency(code='LRD', numeric='430', decimals=2, symbol='$',
                             name=_('Liberian Dollar'),
                             countries=['LIBERIA'])
CURRENCIES['LSL'] = Currency(code='LSL', numeric='426', decimals=2, symbol='', name=_('Loti'),
                             countries=['LESOTHO'])
CURRENCIES['LYD'] = Currency(code='LYD', numeric='434', decimals=3, symbol='',
                             name=_('Libyan Dinar'),
                             countries=['LIBYA'])
CURRENCIES['MAD'] = Currency(code='MAD', numeric='504', decimals=2, symbol='',
                             name=_('Moroccan Dirham'),
                             countries=['MOROCCO', 'WESTERN SAHARA'])
CURRENCIES['MDL'] = Currency(code='MDL', numeric='498', decimals=2, symbol='',
                             name=_('Moldovan Le'),
                             countries=['MOLDOVA, REPUBLIC OF'])
CURRENCIES['MGA'] = Currency(code='MGA', numeric='969', decimals=2, symbol='',
                             name=_('Malagasy Ariary'),
                             countries=['MADAGASCAR'])
CURRENCIES['MKD'] = Currency(code='MKD', numeric='807', decimals=2, symbol='ден',
                             name=_('Denar'),
                             countries=['MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF'])
CURRENCIES['MMK'] = Currency(code='MMK', numeric='104', decimals=2, symbol='', name=_('Kyat'),
                             countries=['MYANMAR'])
CURRENCIES['MNT'] = Currency(code='MNT', numeric='496', decimals=2, symbol='₮',
                             name=_('Tugrik'),
                             countries=['MONGOLIA'])
CURRENCIES['MOP'] = Currency(code='MOP', numeric='446', decimals=2, symbol='', name=_('Pataca'),
                             countries=['MACAO'])
CURRENCIES['MRO'] = Currency(code='MRO', numeric='478', decimals=2, symbol='',
                             name=_('Ouguiya'),
                             countries=['MAURITANIA'])
CURRENCIES['MUR'] = Currency(code='MUR', numeric='480', decimals=2, symbol='₨',
                             name=_('Mauritius Rupee'),
                             countries=['MAURITIUS'])
CURRENCIES['MVR'] = Currency(code='MVR', numeric='462', decimals=2, symbol='',
                             name=_('Rufiyaa'),
                             countries=['MALDIVES'])
CURRENCIES['MWK'] = Currency(code='MWK', numeric='454', decimals=2, symbol='', name=_('Kwacha'),
                             countries=['MALAWI'])
CURRENCIES['MXN'] = Currency(code='MXN', numeric='484', decimals=2, symbol='$',
                             name=_('Mexican Peso'),
                             countries=['MEXICO'])
CURRENCIES['MYR'] = Currency(code='MYR', numeric='458', decimals=2, symbol='RM',
                             name=_('Malaysian Ringgit'),
                             countries=['MALAYSIA'])
CURRENCIES['MZN'] = Currency(code='MZN', numeric='943', decimals=2, symbol='MT',
                             name=_('Mozambique Metical'),
                             countries=['MOZAMBIQUE'])
CURRENCIES['NAD'] = Currency(code='NAD', numeric='516', decimals=2, symbol='$',
                             name=_('Namibia Dollar'),
                             countries=['NAMIBIA'])
CURRENCIES['NGN'] = Currency(code='NGN', numeric='566', decimals=2, symbol='₦', name=_('Naira'),
                             countries=['NIGERIA'])
CURRENCIES['NIO'] = Currency(code='NIO', numeric='558', decimals=2, symbol='C$',
                             name=_('Nicaragua Cordoba'),
                             countries=['NICARAGUA'])
CURRENCIES['NOK'] = Currency(code='NOK', numeric='578', decimals=2, symbol='kr',
                             name=_('Norwegian Krone'),
                             countries=['BOUVET ISLAND', 'NORWAY', 'SVALBARD AND JAN MAYEN'])
CURRENCIES['NPR'] = Currency(code='NPR', numeric='524', decimals=2, symbol='₨',
                             name=_('Nepalese Rupee'),
                             countries=['NEPAL'])
CURRENCIES['NZD'] = Currency(code='NZD', numeric='554', decimals=2, symbol='$',
                             name=_('New Zealand Dollar'),
                             countries=['COOK ISLANDS', 'NEW ZEALAND', 'NIUE', 'PITCAIRN',
                                        'TOKELA'])
CURRENCIES['OMR'] = Currency(code='OMR', numeric='512', decimals=3, symbol='﷼',
                             name=_('Rial Omani'),
                             countries=['OMAN'])
CURRENCIES['PAB'] = Currency(code='PAB', numeric='590', decimals=2, symbol='B/.',
                             name=_('Balboa'),
                             countries=['PANAMA'])
CURRENCIES['PEN'] = Currency(code='PEN', numeric='604', decimals=2, symbol='S/.',
                             name=_('Nuevo Sol'),
                             countries=['PER'])
CURRENCIES['PGK'] = Currency(code='PGK', numeric='598', decimals=2, symbol='', name=_('Kina'),
                             countries=['PAPUA NEW GUINEA'])
CURRENCIES['PHP'] = Currency(code='PHP', numeric='608', decimals=2, symbol='₱',
                             name=_('Philippine Peso'),
                             countries=['PHILIPPINES'])
CURRENCIES['PKR'] = Currency(code='PKR', numeric='586', decimals=2, symbol='₨',
                             name=_('Pakistan Rupee'),
                             countries=['PAKISTAN'])
CURRENCIES['PLN'] = Currency(code='PLN', numeric='985', decimals=2, symbol='zł',
                             name=_('Zloty'),
                             countries=['POLAND'])
CURRENCIES['PYG'] = Currency(code='PYG', numeric='600', decimals=0, symbol='Gs',
                             name=_('Guarani'),
                             countries=['PARAGUAY'])
CURRENCIES['QAR'] = Currency(code='QAR', numeric='634', decimals=2, symbol='﷼',
                             name=_('Qatari Rial'),
                             countries=['QATAR'])
CURRENCIES['RON'] = Currency(code='RON', numeric='946', decimals=2, symbol='lei',
                             name=_('New Romanian Le'),
                             countries=['ROMANIA'])
CURRENCIES['RSD'] = Currency(code='RSD', numeric='941', decimals=2, symbol='Дин.',
                             name=_('Serbian Dinar'),
                             countries=['SERBIA '])
CURRENCIES['RUB'] = Currency(code='RUB', numeric='643', decimals=2, symbol='руб',
                             name=_('Russian Ruble'),
                             countries=['RUSSIAN FEDERATION'])
CURRENCIES['RWF'] = Currency(code='RWF', numeric='646', decimals=0, symbol='',
                             name=_('Rwanda Franc'),
                             countries=['RWANDA'])
CURRENCIES['SAR'] = Currency(code='SAR', numeric='682', decimals=2, symbol='﷼',
                             name=_('Saudi Riyal'),
                             countries=['SAUDI ARABIA'])
CURRENCIES['SBD'] = Currency(code='SBD', numeric='090', decimals=2, symbol='$',
                             name=_('Solomon Islands Dollar'),
                             countries=['SOLOMON ISLANDS'])
CURRENCIES['SCR'] = Currency(code='SCR', numeric='690', decimals=2, symbol='₨',
                             name=_('Seychelles Rupee'),
                             countries=['SEYCHELLES'])
CURRENCIES['SDG'] = Currency(code='SDG', numeric='938', decimals=2, symbol='',
                             name=_('Sudanese Pound'),
                             countries=['SUDAN'])
CURRENCIES['SEK'] = Currency(code='SEK', numeric='752', decimals=2, symbol='kr',
                             name=_('Swedish Krona'),
                             countries=['SWEDEN'])
CURRENCIES['SGD'] = Currency(code='SGD', numeric='702', decimals=2, symbol='$',
                             name=_('Singapore Dollar'),
                             countries=['SINGAPORE'])
CURRENCIES['SHP'] = Currency(
    code='SHP', numeric='654', decimals=2, symbol='£', name=_('Saint Helena Pound'),
    countries=['SAINT HELENA, ASCENSION AND TRISTAN DA CUNHA']
)
CURRENCIES['SLL'] = Currency(
    code='SLL', numeric='694', decimals=2, symbol='', name=_('Leone'), countries=['SIERRA LEONE']
)
CURRENCIES['SOS'] = Currency(
    code='SOS', numeric='706', decimals=2, symbol='S', name=_('Somali Shilling'), countries=['SOMALIA']
)
CURRENCIES['SRD'] = Currency(
    code='SRD', numeric='968', decimals=2, symbol='$', name=_('Surinam Dollar'), countries=['SURINAME']
)
CURRENCIES['STD'] = Currency(
    code='STD', numeric='678', decimals=2, symbol='', name=_('Dobra'), countries=['SAO TOME AND PRINCIPE']
)
CURRENCIES['SVC'] = Currency(
    code='SVC', numeric='222', decimals=2, symbol='$', name=_('El Salvador Colon'), countries=['EL SALVADOR']
)
CURRENCIES['SYP'] = Currency(
    code='SYP', numeric='760', decimals=2, symbol='£', name=_('Syrian Pound'), countries=['SYRIAN ARAB REPUBLIC']
)
CURRENCIES['SZL'] = Currency(
    code='SZL', numeric='748', decimals=2, symbol='', name=_('Lilangeni'), countries=['SWAZILAND']
)
CURRENCIES['THB'] = Currency(code='THB', numeric='764', decimals=2, symbol='฿', name=_('Baht'), countries=['THAILAND'])
CURRENCIES['TJS'] = Currency(
    code='TJS', numeric='972', decimals=2, symbol='', name=_('Somoni'), countries=['TAJIKISTAN']
)
CURRENCIES['TMT'] = Currency(
    code='TMT', numeric='934', decimals=2, symbol='', name=_('Turkmenistan New Manat'), countries=['TURKMENISTAN']
)
CURRENCIES['TND'] = Currency(
    code='TND', numeric='788', decimals=3, symbol='', name=_('Tunisian Dinar'), countries=['TUNISIA']
)
CURRENCIES['TOP'] = Currency(code='TOP', numeric='776', decimals=2, symbol='', name=_('Pa’anga'), countries=['TONGA'])
CURRENCIES['TRY'] = Currency(
    code='TRY', numeric='949', decimals=2, symbol='TL', name=_('Turkish Lira'), countries=['TURKEY']
)
CURRENCIES['TTD'] = Currency(
    code='TTD', numeric='780', decimals=2, symbol='TT$', name=_('Trinidad and Tobago Dollar'),
    countries=['TRINIDAD AND TOBAGO']
)
CURRENCIES['TWD'] = Currency(
    code='TWD', numeric='901', decimals=2, symbol='NT$', name=_('New Taiwan Dollar'),
    countries=['TAIWAN, PROVINCE OF CHINA']
)
CURRENCIES['TZS'] = Currency(
    code='TZS', numeric='834', decimals=2, symbol='', name=_('Tanzanian Shilling'),
    countries=['TANZANIA, UNITED REPUBLIC OF']
)
CURRENCIES['UAH'] = Currency(
    code='UAH', numeric='980', decimals=2, symbol='₴', name=_('Hryvnia'), countries=['UKRAINE']
)
CURRENCIES['UGX'] = Currency(
    code='UGX', numeric='800', decimals=2, symbol='', name=_('Uganda Shilling'), countries=['UGANDA']
)
CURRENCIES['USD'] = Currency(
    code='USD', numeric='840', decimals=2, symbol='$', name=_('US Dollar'),
    countries=[
        'AMERICAN SAMOA', 'BONAIRE, SINT EUSTATIUS AND SABA', 'BRITISH INDIAN OCEAN TERRITORY', 'ECUADOR',
        'EL SALVADOR', 'GUAM', 'HAITI', 'MARSHALL ISLANDS', 'MICRONESIA, FEDERATED STATES OF',
        'NORTHERN MARIANA ISLANDS', 'PALA', 'PANAMA', 'PUERTO RICO', 'TIMOR-LESTE', 'TURKS AND CAICOS ISLANDS',
        'UNITED STATES', 'UNITED STATES MINOR OUTLYING ISLANDS', 'VIRGIN ISLANDS (BRITISH)', 'VIRGIN ISLANDS (US)'
    ]
)
CURRENCIES['UY'] = Currency(
    code='UY', numeric='858', decimals=2, symbol='$', name=_('Peso Uruguayo'), countries=['URUGUAY']
)
CURRENCIES['UZS'] = Currency(
    code='UZS', numeric='860', decimals=2, symbol='лв', name=_('Uzbekistan Sum'), countries=['UZBEKISTAN']
)
CURRENCIES['VEF'] = Currency(
    code='VEF', numeric='937', decimals=2, symbol='Bs', name=_('Bolivar Fuerte'),
    countries=['VENEZUELA, BOLIVARIAN REPUBLIC OF']
)
CURRENCIES['VND'] = Currency(code='VND', numeric='704', decimals=0, symbol='₫', name=_('Dong'), countries=['VIET NAM'])
CURRENCIES['VUV'] = Currency(code='VUV', numeric='548', decimals=0, symbol='', name=_('Vat'), countries=['VANUAT'])
CURRENCIES['WST'] = Currency(code='WST', numeric='882', decimals=2, symbol='', name=_('Tala'), countries=['SAMOA'])
CURRENCIES['XAF'] = Currency(
    code='XAF', numeric='950', decimals=0, symbol='', name=_('CFA Franc BEAC'),
    countries=['CAMEROON', 'CENTRAL AFRICAN REPUBLIC', 'CHAD', 'CONGO', 'EQUATORIAL GUINEA', 'GABON']
)
CURRENCIES['XCD'] = Currency(
    code='XCD', numeric='951', decimals=2, symbol='$', name=_('East Caribbean Dollar'),
    countries=[
        'ANGUILLA', 'ANTIGUA AND BARBUDA', 'DOMINICA', 'GRENADA', 'MONTSERRAT', 'SAINT KITTS AND NEVIS', 'SAINT LUCIA',
        'SAINT VINCENT AND THE GRENADINES'
    ]
)
CURRENCIES['XDR'] = Currency(
    code='XDR', numeric='960', decimals=0, symbol='', name=_('SDR (Special Drawing Right)'),
    countries=['INTERNATIONAL MONETARY FUND (IMF)']
)
CURRENCIES['XOF'] = Currency(
    code='XOF', numeric='952', decimals=0, symbol='', name=_('CFA Franc BCEAO'),
    countries=['BENIN', 'BURKINA FASO', 'CÔTE D\'IVOIRE', 'GUINEA-BISSA', 'MALI', 'NIGER', 'SENEGAL', 'TOGO']
)
CURRENCIES['XPF'] = Currency(
    code='XPF', numeric='953', decimals=0, symbol='', name=_('CFP Franc'),
    countries=['FRENCH POLYNESIA', 'NEW CALEDONIA', 'WALLIS AND FUTUNA']
)
CURRENCIES['YER'] = Currency(
    code='YER', numeric='886', decimals=2, symbol='﷼', name=_('Yemeni Rial'), countries=['YEMEN']
)
CURRENCIES['ZAR'] = Currency(
    code='ZAR', numeric='710', decimals=0, symbol='R', name=_('Rand'), countries=['LESOTHO', 'NAMIBIA', 'SOUTH AFRICA']
)
CURRENCIES['ZMW'] = Currency(
    code='ZMW', numeric='967', decimals=2, symbol='ZK', name=_('Zambian Kwacha'), countries=['ZAMBIA']
)
