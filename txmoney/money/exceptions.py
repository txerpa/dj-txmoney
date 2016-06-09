# coding=utf-8
from __future__ import absolute_import, unicode_literals


class TXMoneyException(Exception):
    """
    Generic txmoney exception
    """

# Money exceptions


class CurrencyDoesNotExist(TXMoneyException):
    """
    Invalid currency
    """
    def __init__(self, code):
        msg = 'No currency with code {} is defined'.format(code)
        super(CurrencyDoesNotExist, self).__init__(msg)


class IncorrectMoneyInputError(TXMoneyException):
    """Invalid input for the Money object"""


class CurrencyMismatch(TXMoneyException, ArithmeticError):
    """ Raised when an operation is not allowed between differing currencies """


class InvalidMoneyOperation(TXMoneyException, TypeError):
    """ Raised when an operation is never allowed """


# Money field exceptions

class NotSupportedLookup(TXMoneyException):
    def __init__(self, lookup):
        msg = 'Lookup {} is not supported for MoneyField'.format(lookup)
        super(NotSupportedLookup, self).__init__(msg)
