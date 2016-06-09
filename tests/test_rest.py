# coding=utf-8
from __future__ import absolute_import, unicode_literals

import pytest

from tests.testapp.serializers import SimpleMoneyModelSerializer
from txmoney.money import Money
from tests.testapp.models import SimpleMoneyModel


@pytest.mark.django_db
class TestRestFrameworkTxmoney(object):

    def test_money_field_serializer(self):
        model = SimpleMoneyModel.objects.create(name='Test', price=Money(amount='100.00', currency='EUR'))
        serializer = SimpleMoneyModelSerializer(model)
        expected = {
            'id': model.pk,
            'name': model.name,
            'price': model.price.amount_rounded,
            'price_currency': model.price.currency,
        }
        assert serializer.data == expected
