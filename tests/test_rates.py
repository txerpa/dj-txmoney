import time
import json

from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase

from txmoney.rates.models import Rate, RateSource
from txmoney.rates.tasks import update_rates

try:
    from mock import patch
except NameError:
    from unittest.mock import patch


class TestRateSource(TestCase):

    def setUp(self):
        self.rs = RateSource.objects.create(name='Test source', base_currency='EUR')

    def test_is_updated(self):
        self.assertTrue(self.rs.is_updated)

    def test_not_is_updated(self):
        with patch.object(self.rs, 'last_update', return_value=datetime.now() - timedelta(1)):
            return self.assertFalse(self.rs.is_updated)


class TestRate(TestCase):

    def setUp(self):
        rs = RateSource.objects.create(name='Test source')
        self.c1 = Rate.objects.create(source=rs, currency='GBP', value=Decimal('1.1176'))
        self.c2 = Rate.objects.create(source=rs, currency='MXN', value=Decimal('0.054069'))


def rates():
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self, parse_float):
            return json.loads(self.json_data, parse_float=parse_float)

    return MockResponse(f"""
    {{
      "disclaimer": "Usage subject to terms: https://openexchangerates.org/terms",
      "license": "https://openexchangerates.org/license",
      "timestamp": {time.time()},
      "base": "USD",
      "rates": {{
        "AED": 3.672969,
        "AFN": 88.525129,
        "ALL": 113.180239,
        "AMD": 507.38406,
        "ANG": 1.789095,
        "AOA": 474.3175,
        "ARS": 108.698417,
        "AUD": 1.364037,
        "AWG": 1.80025,
        "AZN": 1.7,
        "BAM": 1.78315,
        "BBD": 2,
        "BDT": 85.398777,
        "BGN": 1.770648,
        "BHD": 0.376972,
        "BIF": 2006.099069,
        "BMD": 1,
        "BND": 1.351684,
        "BOB": 6.886476,
        "BRL": 5.011,
        "BSD": 1,
        "BTC": 0.00002557099,
        "BTN": 76.831764,
        "BWP": 11.630487,
        "BYN": 3.274576,
        "BZD": 2.001013,
        "CAD": 1.28232,
        "CDF": 2007.799844,
        "CHF": 0.926836,
        "CLF": 0.029266,
        "CLP": 807.55,
        "CNH": 6.32872,
        "CNY": 6.3228,
        "COP": 3747.551333,
        "CRC": 644.587582,
        "CUC": 1,
        "CUP": 25.75,
        "CVE": 101.57,
        "CZK": 22.9209,
        "DJF": 176.728812,
        "DKK": 6.739512,
        "DOP": 54.896486,
        "DZD": 142.54023,
        "EGP": 15.7154,
        "ERN": 15.00001,
        "ETB": 50.918617,
        "EUR": 0.905768,
        "FJD": 2.09825,
        "FKP": 0.759922,
        "GBP": 0.759922,
        "GEL": 3.38,
        "GGP": 0.759922,
        "GHS": 6.998661,
        "GIP": 0.759922,
        "GMD": 53.35,
        "GNF": 8957.029553,
        "GTQ": 7.709012,
        "GYD": 209.260969,
        "HKD": 7.820737,
        "HNL": 24.443961,
        "HRK": 6.8552,
        "HTG": 105.155899,
        "HUF": 346.019301,
        "IDR": 14277.102841,
        "ILS": 3.26916,
        "IMP": 0.759922,
        "INR": 76.373507,
        "IQD": 1448.902544,
        "IRR": 42300,
        "ISK": 131.8,
        "JEP": 0.759922,
        "JMD": 152.452153,
        "JOD": 0.709,
        "JPY": 115.9415,
        "KES": 114.2,
        "KGS": 96.227951,
        "KHR": 4031.39956,
        "KMF": 450.299846,
        "KPW": 900,
        "KRW": 1227.911949,
        "KWD": 0.303533,
        "KYD": 0.827316,
        "KZT": 507.202685,
        "LAK": 11388.3464,
        "LBP": 1515.95601,
        "LKR": 225.844012,
        "LRD": 154.000004,
        "LSL": 15.15218,
        "LYD": 4.628373,
        "MAD": 9.838663,
        "MDL": 18.424772,
        "MGA": 4018.029383,
        "MKD": 55.700197,
        "MMK": 1765.20315,
        "MNT": 2872.125582,
        "MOP": 7.996634,
        "MRU": 36.432733,
        "MUR": 42.95,
        "MVR": 15.45,
        "MWK": 798.394897,
        "MXN": 21.033754,
        "MYR": 4.1875,
        "MZN": 63.83,
        "NAD": 15.25,
        "NGN": 415.84,
        "NIO": 35.7,
        "NOK": 8.96627,
        "NPR": 122.930902,
        "NZD": 1.46036,
        "OMR": 0.384504,
        "PAB": 1,
        "PEN": 3.713285,
        "PGK": 3.51,
        "PHP": 52.24,
        "PKR": 177.94509,
        "PLN": 4.375347,
        "PYG": 6902.464132,
        "QAR": 3.641,
        "RON": 4.48266,
        "RSD": 106.296464,
        "RUB": 117.9,
        "RWF": 1016.883204,
        "SAR": 3.751533,
        "SBD": 8.051577,
        "SCR": 14.41448,
        "SDG": 447,
        "SEK": 9.72205,
        "SGD": 1.359527,
        "SHP": 0.759922,
        "SLL": 11482.649934,
        "SOS": 574.316208,
        "SRD": 20.58,
        "SSP": 130.26,
        "STD": 21382.190504,
        "STN": 22.7,
        "SVC": 8.686682,
        "SYP": 2512,
        "SZL": 15.15678,
        "THB": 33.115987,
        "TJS": 11.287814,
        "TMT": 3.51,
        "TND": 2.9585,
        "TOP": 2.267441,
        "TRY": 14.821675,
        "TTD": 6.740142,
        "TWD": 28.319502,
        "TZS": 2314.5,
        "UAH": 29.831242,
        "UGX": 3596.100104,
        "USD": 1,
        "UYU": 42.768369,
        "UZS": 10920,
        "VES": 4.32325,
        "VND": 22855.5,
        "VUV": 113.968207,
        "WST": 2.618812,
        "XAF": 594.145113,
        "XAG": 0.03855647,
        "XAU": 0.00049867,
        "XCD": 2.70255,
        "XDR": 0.715482,
        "XOF": 594.145113,
        "XPD": 0.0003394,
        "XPF": 108.08692,
        "XPT": 0.00090869,
        "YER": 250.249937,
        "ZAR": 15.1345,
        "ZMW": 17.993015,
        "ZWL": 322
      }}
    }}
    """, 200)


class TestTasks(TestCase):

    @patch('requests.get')
    def test_update_rates_task(self, get_rates_mock):
        get_rates_mock.return_value = rates()

        update_rates()
        get_rates_mock.assert_called_once()
