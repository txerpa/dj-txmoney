# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class TXMoneyRatesConfig(AppConfig):
    name = 'txmoney.rates'
    label = 'txmoney'
    verbose_name = "TXMoney Rates"

    def ready(self):
        from .tasks import update_rates  # noqa
