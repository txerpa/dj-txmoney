# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.forms import MultiWidget, Select, TextInput


class CurrencySelectWidget(MultiWidget):
    """
    Custom widget for entering a value and choosing a currency
    """

    def __init__(self, choices=None, attrs=None):
        widgets = (
            TextInput(attrs=attrs),
            Select(attrs=attrs, choices=choices),
        )
        super(CurrencySelectWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        try:
            return [value.amount, value.currency]
        except:
            return [None, None]
