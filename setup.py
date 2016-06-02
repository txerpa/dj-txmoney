#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from setuptools.command.test import test as test_command


class PyTest(test_command):
    def finalize_options(self):
        test_command.finalize_options(self)
        self.test_args = ['tests']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


def get_version(*file_paths):
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')

version = get_version('txmoney', '__init__.py')

if sys.argv[-1] == 'publish':
    try:
        import wheel
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on github:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

keywords = 'dj-txmoney money currency finance'.split()

tests_require = [
    'pytest-django',
    'pytest-cov',
    'pytest-sugar',
    'tox',
    'django >=1.9',
    'psycopg2',
    'six',
    'wheel',
    'bumpversion',
    'isort',
    'pylint-django',
    'pylint-common'
]

requirements = [
    'six',
    'celery'  # TODO: solo si se usa
]

extras_require = {
    'django': ['Django >= 1.8', ],
}

setup(
    name='dj-txmoney',
    version=version,
    description='Adds support for working with money, currencies and rates.',
    long_description=readme + '\n\n' + history,
    author='Mateu Cànaves Albertí',
    author_email='mateu.canaves@gmail.com',
    url='https://github.com/txerpa/dj-txmoney',
    packages=[
        'txmoney',
    ],
    include_package_data=True,
    license='BSD',
    platforms=['any'],
    zip_safe=False,
    keywords=keywords,
    install_requires=requirements,
    tests_require=tests_require,
    extras_require=extras_require,
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
