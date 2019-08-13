# -*- coding: utf-8 -*-
from django.forms import MultiWidget, TextInput



__all__ = ("MoneyWidget",)


class MoneyWidget(MultiWidget):
    def __init__(
        self,
        amount_widget=TextInput,
        currency_widget=None,
        default_currency=None,
        *args,
        **kwargs
    ):
        self.default_currency = default_currency
        if not currency_widget:
            currency_widget = TextInput()
        widgets = (amount_widget, currency_widget)
        super(MoneyWidget, self).__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value is not None:
            if isinstance(value, (list, tuple)):
                return value
            return [value.amount, value.currency]
        return [None, self.default_currency]
