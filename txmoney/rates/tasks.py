# coding=utf-8
from __future__ import absolute_import, unicode_literals

from celery import shared_task

from ..settings import txmoney_settings as settings


@shared_task
def update_rates():
    """
    Obtiene los tipos de cambio para el 'backend' configurado
    """
    backend_class = settings.DEFAULT_BACKEND_CLASS
    backend = backend_class()
    backend.update_rates()
