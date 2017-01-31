# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand, CommandError

from txmoney.settings import txmoney_settings as settings
from txmoney.settings import import_from_string


class Command(BaseCommand):
    help = "Gets the day's exchange rates"

    def add_arguments(self, parser):
        parser.add_argument('backend_path', nargs='?', help="Exchange backend class")

    def handle(self, *args, **options):
        if options['backend_path']:
            try:
                backend_class = import_from_string(options['backend_path'], '')
            except AttributeError:
                raise CommandError('Cannot find custom backend "%s". Is it correct' % options['backend_path'])
        else:
            backend_class = settings.DEFAULT_BACKEND

        backend = backend_class()
        try:
            backend.update_rates()
        except Exception as e:
            raise CommandError('%s' % e.message)

        self.stdout.write('Successfully updated rates for "%s"' % backend.source_name)
