# coding=utf-8

from django.apps import AppConfig


class TXMoneyRestAppConfig(AppConfig):
    name = 'txmoney.rest'
    verbose_name = "TXMoney DRF Support"

    def ready(self):
        """
        Update Django Rest Framework serializer mappings
        """
        from rest_framework.serializers import ModelSerializer
        from ..money.models import fields
        from .fields import MoneyField

        field_mapping = ModelSerializer.serializer_field_mapping

        # map TXMoney fields to drf-txmoney MoneyField
        field_mapping.update({
            fields.MoneyField: MoneyField,
        })
