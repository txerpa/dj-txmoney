# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django import VERSION
from django.db.models.manager import ManagerDescriptor


def setup_managers(sender):
    from .money.models.managers import money_manager

    if VERSION >= (1, 10):
        for manager in [m for m in sender._meta.managers if m.name == 'objects']:
            setattr(sender, manager.name, ManagerDescriptor(money_manager(manager)))
    else:
        sender.copy_managers([
            (_id, name, money_manager(manager))
            for _id, name, manager in sender._meta.concrete_managers if name == 'objects'
        ])
