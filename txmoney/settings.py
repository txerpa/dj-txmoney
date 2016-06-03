# coding=utf-8
"""
This module is largely inspired by django-rest-framework settings.

Settings for txdmoney are all namespaced in the TXDMONEY setting.
For example your project's `settings.py` file might look like this:

TXDMONEY = {
    'DEFAULT_BACKEND': 'txdmoney.backends.OpenExchangeBackend',
    'BASE_CURRENCY': 'EUR'
    'BACKEND_KEY': '00000000000000'
}

This module provides the `txmoney_settings` object, that is used to access
txdmoney settings, checking for user settings first, then falling
back to the defaults.
"""
from __future__ import absolute_import, unicode_literals

import importlib

import six

from django.conf import settings

USER_SETTINGS = getattr(settings, str('TXMONEY'), None)

DEFAULTS = {
    'DEFAULT_BACKEND': 'txmoney.backends.OpenExchangeBackend',
    'BACKEND_KEY': '',
    'BASE_CURRENCY': 'USD',
    'SAME_BASE_CURRENCY': True,

    'OPENEXCHANGE_NAME': 'openexchangerates.org',
    'OPENEXCHANGE_URL': 'https://openexchangerates.org/api/latest.json',
    'OPENEXCHANGE_BASE_CURRENCY': 'USD',
}

# List of settings that cannot be empty
MANDATORY = (
    'DEFAULT_BACKEND',
    'BACKEND_KEY',
)

# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    'DEFAULT_BACKEND',
)


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation, then perform the necessary import or imports.
    :param val: setting value
    :param setting_name: setting name
    """
    if isinstance(val, six.string_types):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    :param val: setting value
    :param setting_name: setting name
    """
    try:
        parts = val.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except ImportError as e:
        msg = 'Could not import "{}" for setting "{}". {}: {}.'.format(val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class TXMoneySettings:
    """
    A settings object, that allows txdmoney settings to be accessed as properties.
    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """

    def __init__(self, user_settings=None, defaults=None, import_strings=None, mandatory=None):
        self.user_settings = user_settings or {}
        self.defaults = defaults or {}
        self.import_strings = import_strings or ()
        self.mandatory = mandatory or ()

    def __getattr__(self, attr):
        if attr not in self.defaults.keys():
            raise AttributeError('Invalid txmoney setting: "{}"'.format(attr))

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if val and attr in self.import_strings:
            val = perform_import(val, attr)

        self.validate_setting(attr, val)

        # Cache the result
        setattr(self, attr, val)
        return val

    def validate_setting(self, attr, val):
        if not val and attr in self.mandatory:
            raise AttributeError('txmoney setting: "{}" is mandatory'.format(attr))


txmoney_settings = TXMoneySettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS, MANDATORY)