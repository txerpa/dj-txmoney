# coding=utf-8
from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task

from ..settings import txmoney_settings as settings

logger = logging.getLogger(__name__)


@shared_task
def update_rates():
    """
    Obtiene los tipos de cambio para el 'backend' configurado
    """
    backend_class = settings.DEFAULT_BACKEND
    backend = backend_class()
    backend.update_rates()
