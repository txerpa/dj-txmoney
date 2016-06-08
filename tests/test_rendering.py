from __future__ import absolute_import, unicode_literals

import pytest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from .testapp.views import instance_view, model_from_db_view, model_view


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

        self.assertContains(response, 'money|0 JPY|')
        self.assertContains(response, 'money.amount|0|')
        self.assertContains(response, 'money.currency|JPY|')

    @pytest.mark.skipif('sqlite' in settings.DATABASES['default']['ENGINE'],
                        reason='SQLite can not represent trailing zeros')
    def test_model_from_db_view_trailing_zeros(self):
        url = reverse(model_from_db_view, kwargs={'amount': '542.100', 'currency': 'USD'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'money|542.10 USD|')
        self.assertContains(response, 'money.amount|542.10|')
        self.assertContains(response, 'money.currency|USD|')
