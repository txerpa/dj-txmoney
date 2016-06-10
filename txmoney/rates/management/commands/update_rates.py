# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand, CommandError

from txmoney.settings import txmoney_settings as settings
from txmoney.settings import import_from_string


class Command(BaseCommand):
    args = '<backend_path>'
    help = 'Actualiza tarifas para el origen configurado'

    def handle(self, *args, **options):
        if args:
            try:
                backend_class = import_from_string(args[0], '')
            except AttributeError:
                raise CommandError('Cannot find custom backend {}. Is it correct'.format(args[0]))
        else:
            backend_class = settings.DEFAULT_BACKEND

        try:
            backend = backend_class()
            backend.update_rates()
        except Exception as e:
            raise CommandError('Error during rate update: {}'.format(e))

        self.stdout.write('Successfully updated rates for "{}"'.format(backend_class))
