# coding=utf-8
from __future__ import absolute_import

import factory

from txmoney.models import *


class RateSourceFactory(factory.DjangoModelFactory):
    class Meta:
        model = RateSource

    name = factory.Faker('domain_name')


class RateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rate

    source = factory.SubFactory(RateSourceFactory)
    currency = factory.Faker('currency_code')
    value = factory.Faker('pydecimal', left_digits=1, right_digits=6, positive=True)
