# coding=utf-8

from django.core.management.base import BaseCommand, CommandError

from ....settings import import_from_string, txmoney_settings


class Command(BaseCommand):
    help = "Gets the day's exchange rates"

    def add_arguments(self, parser):
        parser.add_argument('backend_path', nargs='?', help="Exchange backend class")

    def handle(self, *args, **options):
        if options['backend_path']:
            try:
                backend_class = import_from_string(options['backend_path'], '')
            except AttributeError:
                raise CommandError(f'Cannot find custom backend "{options["backend_path"]}". Is it correct')
        else:
            backend_class = txmoney_settings.DEFAULT_BACKEND_CLASS

        backend = backend_class()
        try:
            backend.update_rates()
        except Exception as e:
            raise CommandError(f'{e}')

        self.stdout.write(f'Successfully updated rates for "{backend.source_name}"')
