# coding=utf-8

from rest_framework import serializers

from tests.testapp.models import SimpleMoneyModel


class SimpleMoneyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimpleMoneyModel
        fields = '__all__'
