from django import forms

from txmoney.money import Money, CURRENCIES


class MoneyField(forms.MultiValueField):
    """
    A MultiValueField to represent both the quantity of money and the currency
    """

    def __init__(self, choices=None, decimal_places=2, max_digits=12, *args, **kwargs):
        # Note that we catch args and kwargs that must only go to one field
        # or the other. The rest of them pass onto the decimal field.
        choices = choices or [
            (c.code, '{0} - {1}'.format(c.code, c.name),) for i, c in sorted(CURRENCIES.items())]

        self.widget = CurrencySelectWidget(choices)

        fields = (
            forms.DecimalField(*args, decimal_places=decimal_places, max_digits=max_digits, **kwargs),
            forms.ChoiceField(choices=choices)
        )
        super(MoneyField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        """
        Take the two values from the request and return a single data value
        """
        if data_list:
            return Money(*data_list)
        return None


class CurrencySelectWidget(forms.MultiWidget):
    """
    Custom widget for entering a value and choosing a currency
    """

    def __init__(self, choices=None, attrs=None):
        widgets = (
            forms.TextInput(attrs=attrs),
            forms.Select(attrs=attrs, choices=choices),
        )
        super(CurrencySelectWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        try:
            return [value.amount, value.currency]
        except:
            return [None, None]
