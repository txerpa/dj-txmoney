# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class RTxmoneyAppConfig(AppConfig):
    name = 'rest_framework_txmoney'

    def ready(self):
        """
        update Django Rest Framework serializer mappings
        """
        from txmoney.money import models
        from rest_framework.serializers import ModelSerializer
        from .fields import MoneyField

        try:
            # drf 3.0
            field_mapping = ModelSerializer._field_mapping.mapping
        except AttributeError:
            # drf 3.1
            field_mapping = ModelSerializer.serializer_field_mapping

        # map TXMoney fields to drf-txmoney MoneyField
        field_mapping.update({
            models.MoneyField: MoneyField,
        })
