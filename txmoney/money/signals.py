# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.db.models.signals import class_prepared

from txmoney.compat import setup_managers


def patch_managers(sender, **kwargs):
    """
    Patches models managers.
    """
    if sender._meta.proxy_for_model:
        has_money_field = hasattr(sender._meta.proxy_for_model._meta, 'has_money_field')
    else:
        has_money_field = hasattr(sender._meta, 'has_money_field')

    if has_money_field:
        setup_managers(sender)


class_prepared.connect(patch_managers)
