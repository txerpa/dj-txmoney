# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class TXMoneyRestAppConfig(AppConfig):
    name = 'txmoney.rest'
    label = 'txmoneyrest'
    verbose_name = "TXMoney drf support"

    def ready(self):
        """
        update Django Rest Framework serializer mappings
        """
        from rest_framework.serializers import ModelSerializer
        from ..money.models import fields
        from .fields import MoneyField

        field_mapping = ModelSerializer.serializer_field_mapping

        # map TXMoney fields to drf-txmoney MoneyField
        field_mapping.update({
            fields.MoneyField: MoneyField,
        })
