# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class RTxmoneyAppConfig(AppConfig):
    name = 'txmoney.rest'
    label = 'txmoney_rest_framework'

    def ready(self):
        """
        update Django Rest Framework serializer mappings
        """
        from txmoney.money import models
        from rest_framework.serializers import ModelSerializer
        from .fields import MoneyField

        field_mapping = ModelSerializer.serializer_field_mapping

        # map TXMoney fields to drf-txmoney MoneyField
        field_mapping.update({
            models.MoneyField: MoneyField,
        })
