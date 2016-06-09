# coding=utf-8
from __future__ import absolute_import, unicode_literals

import json
from abc import ABCMeta, abstractmethod
from decimal import Decimal

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction

from six import iteritems, with_metaclass

from six.moves.urllib.request import urlopen

from ..settings import txmoney_settings as settings
from ..utils import parse_rates_to_base_currency
from .exceptions import TXRateBackendError
from .models import Rate, RateSource


class BaseRateBackend(with_metaclass(ABCMeta)):
    """Abstract base class API for exchange backends"""

    _source_name = None
    _base_currency = None

    def __init__(self, source_name, base_currency):
        # TODO: validate currency
        self._source_name = source_name
        self._base_currency = base_currency

    @property
    def source_name(self):
        """Return the source backend name"""
        return self._source_name

    @property
    def base_currency(self):
        """Return the base currency"""
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
                # Force update last_update date on origin
                source.save()
        except Exception:
            raise TXRateBackendError('Error during {} rates update'.format(self.source_name))


class OpenExchangeBackend(BaseRateBackend):
    def __init__(self):
        super(OpenExchangeBackend, self).__init__(
            settings.OPENEXCHANGE_NAME, settings.OPENEXCHANGE_BASE_CURRENCY
        )

        if not settings.OPENEXCHANGE_URL:
            raise ImproperlyConfigured('OPENEXCHANGE_URL setting should not be empty when using OpenExchangeBackend')

        if not settings.BACKEND_KEY:
            raise ImproperlyConfigured('BACKEND_KEY setting should not be empty when using OpenExchangeBackend')

        self.url = '{}?app_id={}'.format(settings.OPENEXCHANGE_URL, settings.BACKEND_KEY)

    def get_rates_from_source(self):
        try:
            data = urlopen(self.url).read().decode("utf-8")
            rates = json.loads(data, parse_float=Decimal)['rates']
            # rates = clean_rates(rates) TODO: clean rates

            if settings.SAME_BASE_CURRENCY and settings.BASE_CURRENCY != settings.OPENEXCHANGE_BASE_CURRENCY:
                rates = parse_rates_to_base_currency(rates, settings.BASE_CURRENCY)
        except Exception:
            raise TXRateBackendError('Error retrieving data from {}'.format(self.url))

        return rates
