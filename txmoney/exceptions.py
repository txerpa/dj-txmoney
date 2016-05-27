# coding=utf-8
from __future__ import absolute_import, unicode_literals


class TXMoneyException(Exception):
    """
    Generic txmoney exception
    """


# Backend exceptions

class RateBackendError(TXMoneyException):
    """
    Base exceptions raised by RateBackend implementations
    """


class RateDoesNotExist(TXMoneyException):
    """
    Base exceptions raised by RateBackend implementations
    """

    def __init__(self, currency, date):
        msg = 'No {} rate at {}'.format(currency, date)
        super(RateDoesNotExist, self).__init__(msg)


# Money exceptions

class CurrencyDoesNotExist(TXMoneyException):
    """
    Invalid currency
    """

    def __init__(self, code):
        msg = 'No currency with code {} is defined'.format(code)
        super(CurrencyDoesNotExist, self).__init__(msg)


class CurrencyMismatch(TXMoneyException, ValueError):
    """
    Invalid operation between money objects of different currencies
    """

    def __init__(self, a, b, op):
        msg = 'Unsupported operation "{}" between money in "{}" and "{}"'.format(op, a, b)
        super(CurrencyMismatch, self).__init__(msg)


class InvalidOperandType(TXMoneyException, TypeError):
    """
    Invalid operation between money object and other object
    """

    def __init__(self, operand, operation):
        msg = 'Unsupported operation "{}" between money and "{}"'.format(operation, type(operand))
        super(InvalidOperandType, self).__init__(msg)


# Money field exceptions

class NotSupportedLookup(TXMoneyException):
    def __init__(self, lookup):
        msg = 'Lookup {} is not supported for MoneyField'.format(lookup)
        super(NotSupportedLookup, self).__init__(msg)
