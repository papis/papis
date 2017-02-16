# -*- coding: utf-8 -*-
#
# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too

from __future__ import print_function

import os.path
import subprocess
import sys

from setuptools import setup

from papis import __version__


def generate_readme_rst():
    """
    Generate README.rst from README.md via pandoc.

    In case of errors, we show a message having the error that we got and
    exit the program.
    """

    pandoc_cmd = [
        'pandoc',
        '--from=markdown',
        '--to=rst',
        '--output=README.rst',
        'README.md'
    ]

    if os.path.exists('README.rst'):
        return
    try:
        subprocess.call(pandoc_cmd)
    except (IOError, OSError) as e:
        print('Could not run "pandoc". Error: %s' % e, file=sys.stderr)
        print('Generating only a stub instead of the real documentation.')


def read_file(filename, alt=None):
    """
    Read the contents of filename or give an alternative result instead.
    """
    lines = None

    try:
        with open(filename) as f:
            lines = f.read()
    except IOError:
        lines = [] if alt is None else alt
    return lines


generate_readme_rst()

long_description = read_file(
    'README.rst',
    'Generate README.rst from README.md via pandoc!\n\nExample: '
    'pandoc --from=markdown --to=rst --output=README.rst README.md'
)
requirements = read_file('requirements.txt')
dev_requirements = read_file('requirements-dev.txt')

trove_classifiers = [
    'Environment :: Console',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python',
    'Topic :: Education',
]

setup(
    name='papis',
    version=__version__,
    maintainer='Alejandro Gallo',
    maintainer_email='aamsgallo@gmail.com',
    license='LGPL',
    url='https://github.com/alejandrogallo/papis',
    install_requires=requirements,
    extras_require=dict(
        dev=dev_requirements
    ),

    description='Simple program to manage literature',
    long_description=long_description,
    keywords=['paper', 'books', 'bibtex', 'management', 'cli', 'biliography'],
    classifiers=trove_classifiers,

    packages=["papis"],
    test_suite=["papis.tests"],
    entry_points=dict(
        console_scripts=[
            'papis=papis.papis:main'
        ]
    ),

    platforms=['any'],
)
