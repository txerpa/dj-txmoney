# coding=utf-8
from __future__ import absolute_import, unicode_literals


class TXRateBackendError(Exception):
    """
    Base exceptions raised by RateBackend implementations
    """


class RateDoesNotExist(TXRateBackendError):
    """
    Invalid Rate
    """
    def __init__(self, currency, date):
        msg = 'No {} rate at {}'.format(currency, date)
        super(RateDoesNotExist, self).__init__(msg)
