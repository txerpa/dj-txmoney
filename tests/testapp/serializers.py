# coding=utf-8
from __future__ import absolute_import, unicode_literals

from rest_framework import serializers

from tests.testapp.models import SimpleMoneyModel


class SimpleMoneyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimpleMoneyModel
        fields = '__all__'
