# coding=utf-8


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
        msg = f'No currency with code {code} is defined'
        super(CurrencyDoesNotExist, self).__init__(msg)


class IncorrectMoneyInputError(TXMoneyException):
    """
    Invalid input for the Money object
    """


class CurrencyMismatch(TXMoneyException, ArithmeticError):
    """
    Raised when an operation is not allowed between differing currencies
    """


class InvalidMoneyOperation(TXMoneyException, TypeError):
    """
    Raised when an operation is never allowed
    """

# Field exceptions


class NotSupportedLookup(TXMoneyException):
    def __init__(self, lookup):
        super(NotSupportedLookup, self).__init__(f'Lookup "{lookup}" is not supported for MoneyField')
