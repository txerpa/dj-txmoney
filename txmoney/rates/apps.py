# coding=utf-8

from django.apps import AppConfig


class TXMoneyRatesConfig(AppConfig):
    name = 'txmoney.rates'
    label = 'txmoney'
    verbose_name = "TXMoney Rates"

    def ready(self):
        pass
