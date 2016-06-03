from __future__ import print_function

from django import forms
from django.shortcuts import get_object_or_404, render_to_response

from tests.testapp.models import SimpleMoneyModel
from txmoney.forms import MoneyField
from txmoney.money import Money
from txmoney.settings import txmoney_settings as settings


class SampleForm(forms.Form):
    price = MoneyField()


class SampleModelForm(forms.ModelForm):
    class Meta:
        model = SimpleMoneyModel

        fields = ('name', 'price',)


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


def model_form_view(request, amount='0', currency=settings.BASE_CURRENCY):
    cleaned_data = {}
    if request.method == 'POST':
        form = SampleModelForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            form.save()
            # Most views would redirect here but we continue so we can render the data
    else:
        form = SampleModelForm(initial={'price': Money(amount, currency)})

    return render_to_response('form.html', {'form': form, 'cleaned_data': cleaned_data})


def regular_form(request):
    if request.method == 'POST':
        form = SampleForm(request.POST)

        if form.is_valid():
            price = form.cleaned_data['price']
            return render_to_response('form.html', {'price': price})
    else:
        form = SampleForm()
    return render_to_response('form.html', {'form': form})


def regular_form_edit(request, id):
    instance = get_object_or_404(SimpleMoneyModel, pk=id)
    if request.method == 'POST':
        form = SampleForm(request.POST, initial={'price': instance.price})

        if form.is_valid():
            price = form.cleaned_data['price']
            return render_to_response('form.html', {'price': price})
    else:
        form = SampleForm(initial={'price': instance.price})
    return render_to_response('form.html', {'form': form})


def model_form_edit(request, id):
    instance = get_object_or_404(SimpleMoneyModel, pk=id)
    if request.method == 'POST':
        form = SampleModelForm(request.POST, instance=instance)

        if form.is_valid():
            price = form.cleaned_data['price']
            form.save()
            return render_to_response('form.html', {'price': price})
    else:
        form = SampleModelForm(instance=instance)
    return render_to_response('form.html', {'form': form})
