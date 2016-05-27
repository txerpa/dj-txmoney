# coding=utf-8
from django.db import transaction


class BaseRateBackend(object):
    @transaction.atomic
    def update_rates(self):
        pass


class OpenExchangeBackend(BaseRateBackend):
    pass
