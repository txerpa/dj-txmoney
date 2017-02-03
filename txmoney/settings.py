# coding=utf-8
"""
This module is largely inspired by django-rest_framework-framework settings.

Settings for TXMoney are all namespaced in the TXMONEY setting.
For example your project's `settings.py` file might look like this:

TXMONEY = {
    'DEFAULT_BACKEND_CLASS': 'txmoney.rates.backends.OpenExchangeBackend',
    'BASE_CURRENCY': 'EUR',
    'OPENEXCHANGE': {
        'app_id': '<some_app_id>'
    }
}

This module provides the `txmoney_settings` object, that is used to access
TXMoney settings, checking for user settings first, then falling
back to the defaults.
"""
from __future__ import absolute_import, unicode_literals

from importlib import import_module

from django.conf import settings
from django.utils.six import string_types

DEFAULTS = {
    'DEFAULT_BACKEND_CLASS': 'txmoney.rates.backends.OpenExchangeBackend',
    'DEFAULT_CURRENCY': 'USD',
    'SAME_BASE_CURRENCY': True,

    'OPENEXCHANGE': {
        'name': 'openexchangerates.org',
        'url': 'https://openexchangerates.org',
        'base_currency': 'USD',
        'app_id': ''
    }
}

# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    'DEFAULT_BACKEND_CLASS',
)


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, string_types):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        parts = val.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as exp:
        msg = "Could not import '%s' for TXMONEY setting '%s'. %s: %s." % (
            val, setting_name, exp.__class__.__name__, exp
        )
        raise ImportError(msg)


class TXMoneySettings(object):
    """
    A settings object, that allows TXMoney settings to be accessed as properties.
    For example:

        from txmoney.settings import txmoney_settings
        print(txmoney_settings.DEFAULT_RENDERER_CLASSES)

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """
    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'TXMONEY', {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid TXMoney setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if val and attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        setattr(self, attr, val)
        return val


txmoney_settings = TXMoneySettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_api_settings(**kwargs):
    global txmoney_settings
    setting, value = kwargs['setting'], kwargs['value']
    if setting == 'TXMONEY':
        txmoney_settings = TXMoneySettings(value, DEFAULTS, IMPORT_STRINGS)
