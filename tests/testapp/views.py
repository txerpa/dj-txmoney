from __future__ import print_function

from django.shortcuts import render_to_response

from tests.testapp.models import SimpleMoneyModel
from txmoney.money import Money
from txmoney.settings import txmoney_settings as settings


def instance_view(request):
    money = Money('0.0', 'JPY')
    return render_to_response('view.html', {'money': money})


def model_view(request):
    instance = SimpleMoneyModel(price=Money('0.0', 'JPY'))
    money = instance.price
    return render_to_response('view.html', {'money': money})


def model_from_db_view(request, amount='0', currency=settings.BASE_CURRENCY):
    # db roundtrip
    instance = SimpleMoneyModel.objects.create(price=Money(amount, currency))
    instance = SimpleMoneyModel.objects.get(pk=instance.pk)

    money = instance.price
    return render_to_response('view.html', {'money': money})
