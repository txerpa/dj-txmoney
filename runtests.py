# coding=utf-8
from __future__ import absolute_import, unicode_literals

import argparse
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.testapp.settings'


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--postgres', action='store_true')

    return parser


def parse_args(args=None):
    return make_parser().parse_args(args)


def runtests():
    import pytest

    args = parse_args()
    if args.postgres:
        os.environ['DATABASE_ENGINE'] = 'django.db.backends.postgresql_psycopg2'
    argv = [sys.argv[0], 'tests']

    errno = pytest.main(argv)
    sys.exit(errno)


if __name__ == '__main__':
    runtests()
