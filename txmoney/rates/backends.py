# coding=utf-8
from __future__ import absolute_import, unicode_literals

from abc import ABCMeta, abstractmethod
from decimal import Decimal

import requests
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils.six import iteritems, with_metaclass

from ..settings import txmoney_settings as settings
from .exceptions import TXRateBackendError
from .models import Rate, RateSource
from .utils import parse_rates_to_base_currency


class BaseRateBackend(with_metaclass(ABCMeta)):
    """
    Abstract base class API for exchange backends
    """

    def __init__(self, source_name, base_currency):
        self._source_name = source_name
        self._base_currency = base_currency

    @property
    def source_name(self):
        return self._source_name

    @property
    def base_currency(self):
        return self._base_currency

    @abstractmethod
    def get_rates_from_source(self):
        """
        Return a dictionary that maps currency code with its rate value
        """

    @transaction.atomic
    def update_rates(self):
        """
        Creates or updates rates for a source
        """
        try:
            source, created = RateSource.objects.get_or_create(name=self.source_name, base_currency=self.base_currency)

            if created or not source.is_updated:
                rates = []
                for currency, value in iteritems(self.get_rates_from_source()):
                    rates.append(Rate(source=source, currency=currency, value=value))

                Rate.objects.bulk_create(rates)
                source.save()  # Force update last_update date on rate source
        except Exception as e:
            raise TXRateBackendError("Error during '%s' rates update. %s" % (self.source_name, e.message))


class OpenExchangeBackend(BaseRateBackend):
    def __init__(self):
        super(OpenExchangeBackend, self).__init__(
            settings.OPENEXCHANGE_NAME, settings.OPENEXCHANGE_BASE_CURRENCY
        )

        if not settings.OPENEXCHANGE_URL:
            raise ImproperlyConfigured('OPENEXCHANGE URL setting should not be empty when using OpenExchangeBackend')

        if not settings.OPENEXCHANGE_APP_ID:
            raise ImproperlyConfigured('OPENEXCHANGE APP_ID setting should not be empty when using OpenExchangeBackend')

        self.url = '{}?app_id={}'.format(settings.OPENEXCHANGE_URL, settings.BACKEND_KEY)

    def get_rates_from_source(self):
        try:
            r = requests.get(self.url, encoding='utf-8')
            rates = r.json(parse_float=Decimal)['rates']

            if settings.SAME_BASE_CURRENCY and settings.DEFAULT_CURRENCY != settings.OPENEXCHANGE_BASE_CURRENCY:
                rates = parse_rates_to_base_currency(rates, settings.OPENEXCHANGE_BASE_CURRENCY)
        except Exception as e:
            raise TXRateBackendError("Error retrieving rates from '%s'. %s" % (self.url, e.message))

        return rates
