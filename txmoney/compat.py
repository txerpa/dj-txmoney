# -*- coding: utf-8 -*-
# flake8: noqa
from django import VERSION
from django.db.models.manager import ManagerDescriptor

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen


def setup_managers(sender):
    from txmoney.money.models.managers import money_manager

    if VERSION >= (1, 10):
        for manager in filter(lambda m: m.name == 'objects', sender._meta.managers):
            setattr(sender, manager.name, ManagerDescriptor(money_manager(manager)))
    else:
        sender.copy_managers([
            (_id, name, money_manager(manager))
            for _id, name, manager in sender._meta.concrete_managers if name == 'objects'
        ])
