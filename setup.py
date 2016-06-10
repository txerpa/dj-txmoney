#!/usr/bin/env python
# coding=utf-8
from __future__ import absolute_import, unicode_literals

import os
import re


try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


def get_version(*file_paths):
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')

version = get_version('txmoney', '__init__.py')

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')
keywords = 'dj-txmoney txmoney money currency finance'.split()

install_requires = [
    'Django>=1.8.1,<1.10',
    'six',
]

testing_extras = [
    # Required for running the tests
    'mock',
    'tox',
    'pytest',
    'pytest-django',
    'pytest-sugar',

    # For coverage and PEP8 linting
    'coverage>=4.1',
    'flake8>=2.2.0',
]

documentation_extras = [
    'Sphinx>=1.3.1',
    'sphinx-autobuild>=0.5.2',
    'sphinx_rtd_theme>=0.1.8',
    'sphinxcontrib-spelling==2.1.1',
    'pyenchant==1.6.6',
]

setup(
    name='dj-txmoney',
    version=version,
    description='Adds support for working with money, currencies and rates.',
    long_description=readme + '\n\n' + history,
    author='Mateu Cànaves Albertí',
    author_email='mateu.canaves@gmail.com',
    url='https://github.com/txerpa/dj-txmoney',
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'postgresql': ['psycopg2>=2.6'],
        'rates': ['celery>=3.0.0'],
        'rest': ['djangorestframework>=3.1.0'],
        'testing': testing_extras,
        'docs': documentation_extras,
    },
    license='BSD',
    zip_safe=False,
    keywords=keywords,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
)
