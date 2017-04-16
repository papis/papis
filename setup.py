# -*- coding: utf-8 -*-
#
# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too

from __future__ import print_function

from setuptools import setup

from papis import __version__


setup(
    name='papis',
    version=__version__,
    maintainer='Alejandro Gallo',
    maintainer_email='aamsgallo@gmail.com',
    license='LGPL',
    url='https://github.com/alejandrogallo/papis',
    install_requires=[
       "argcomplete",
       "configparser",
       "arxiv2bib",
       "argparse",
       "PyYAML",
       "pdfminer2"
        ],
    extras_require=dict(
        dev=[]
    ),

    description='Simple program to manage literature',
    long_description='Simple program to manage literature',
    keywords=[
        'document',
        'books',
        'bibtex',
        'management',
        'cli',
        'biliography'
        ],
    packages=["papis"],
    test_suite="papis.tests",
    entry_points=dict(
        console_scripts=[
            'papis=papis.papis:main'
        ]
    ),

    platforms=['any'],
)
