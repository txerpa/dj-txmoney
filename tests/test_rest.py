# coding=utf-8
from __future__ import absolute_import, unicode_literals

import pytest

from tests.testapp.models import SimpleMoneyModel
from tests.testapp.serializers import SimpleMoneyModelSerializer
from txmoney.money.models.models import Money


@pytest.mark.django_db
class TestRestFrameworkTxmoney(object):

    def test_money_field_serializer(self):
        model = SimpleMoneyModel.objects.create(amount=Money(amount='100.00', currency='EUR'))
        serializer = SimpleMoneyModelSerializer(model)
        expected = {
            'id': model.pk,
            'amount': model.amount.amount_rounded,
            'amount_currency': model.amount.currency,
        }
        assert serializer.data == expected
