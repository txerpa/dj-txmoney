from abc import ABC, abstractmethod
from decimal import Decimal

import requests
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction

from ..settings import txmoney_settings as settings
from .exceptions import TXRateBackendError
from .models import Rate, RateSource
from .utils import parse_rates_to_base_currency


class BaseRateBackend(ABC):
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
                for currency, value in self.get_rates_from_source().items():
                    rates.append(Rate(source=source, currency=currency, value=value))

                Rate.objects.bulk_create(rates)
                source.save()  # Force update last_update date on rate source
        except Exception as e:
            raise TXRateBackendError(f'Error during "{self.source_name}" rates update. {e}')


class OpenExchangeBackend(BaseRateBackend):
    def __init__(self):
        super(OpenExchangeBackend, self).__init__(
            settings.OPENEXCHANGE_NAME, settings.OPENEXCHANGE_BASE_CURRENCY
        )

        if not settings.OPENEXCHANGE_URL:
            raise ImproperlyConfigured('OPENEXCHANGE URL setting should not be empty when using OpenExchangeBackend')

        if not settings.OPENEXCHANGE_APP_ID:
            raise ImproperlyConfigured('OPENEXCHANGE APP_ID setting should not be empty when using OpenExchangeBackend')

        self.url = f'{settings.OPENEXCHANGE_URL}?app_id={settings.OPENEXCHANGE_APP_ID}'

    def get_rates_from_source(self):
        try:
            r = requests.get(self.url)
            rates = r.json(parse_float=Decimal)['rates']

            if settings.SAME_BASE_CURRENCY and settings.DEFAULT_CURRENCY != settings.OPENEXCHANGE_BASE_CURRENCY:
                rates = parse_rates_to_base_currency(rates, settings.OPENEXCHANGE_BASE_CURRENCY)
        except Exception as e:
            raise TXRateBackendError(f'Error retrieving rates from "{self.url}". {e}')

        return rates
