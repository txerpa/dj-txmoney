# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.core.signals import setting_changed

from .rates.apps import TXMoneyRatesConfig
from .settings import reload_api_settings


class TXMoneyConfig(TXMoneyRatesConfig):
    label = 'txmoney'

    def ready(self):
        setting_changed.connect(reload_api_settings)
