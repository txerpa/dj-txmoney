from __future__ import unicode_literals

import pytest
from tests.testapp.models import SimpleMoneyModel
from tests.testapp.views import (
    instance_view, model_form_view, model_from_db_view, model_view
)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client, TestCase


class TestView(TestCase):
    def setUp(self):
        self.client = Client()

    def test_instance_view(self):
        url = reverse(instance_view)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'money|0.0 JPY|')
        self.assertContains(response, 'money.amount|0.0|')
        self.assertContains(response, 'money.currency|JPY|')

    def test_model_view(self):
        url = reverse(model_view)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'money|0.0 JPY|')
        self.assertContains(response, 'money.amount|0.0|')
        self.assertContains(response, 'money.currency|JPY|')

    @pytest.mark.skipif('sqlite' in settings.DATABASES['default']['ENGINE'],
                        reason='SQLite can not represent 0.0 values')
    def test_model_from_db_view_zero_with_trailing_zeros(self):
        url = reverse(model_from_db_view, kwargs={'amount': '0.0', 'currency': 'JPY'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'money|0.0 JPY|')
        self.assertContains(response, 'money.amount|0.0|')
        self.assertContains(response, 'money.currency|JPY|')

    @pytest.mark.skipif('sqlite' in settings.DATABASES['default']['ENGINE'],
                        reason='SQLite can not represent trailing zeros')
    def test_model_from_db_view_trailing_zeros(self):
        url = reverse(model_from_db_view, kwargs={'amount': '542.100', 'currency': 'JPY'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'money|JPY 542.100|')
        self.assertContains(response, 'money.amount|542.100|')
        self.assertContains(response, 'money.currency|JPY|')


class TestEditView(TestCase):
    def setUp(self):
        self.client = Client()

    def test_form_GET(self):
        url = reverse(model_form_view, kwargs={'amount': '987.00', 'currency': 'JPY'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'value="987.00"')
        self.assertContains(response, '<option value="JPY" selected="selected">JPY - Yen</option>')

    def test_form_GET_zero(self):
        url = reverse(model_form_view, kwargs={'amount': '0.0', 'currency': 'JPY'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'value="0.0"')
        self.assertContains(response, '<option value="JPY" selected="selected">JPY - Yen</option>')

    def test_form_POST(self):
        url = reverse(model_form_view, kwargs={'amount': '555.5', 'currency': 'JPY'})

        # We intentionally use decimals with a typically non-decimal currency
        response = self.client.post(url, {
            'name': 'ABC',
            'price_0': '555.5',
            'price_1': 'JPY',
        })

        # Find the object we created...
        obj = SimpleMoneyModel.objects.last()
        self.assertEqual(str(obj.price), '555.5 JPY')

        self.assertContains(response, '|item:name|value:ABC|')
        self.assertContains(response, '|item:price|value:555.5 JPY|')
