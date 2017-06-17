# -*- coding: utf-8 -*-
#
# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too

from __future__ import print_function

from setuptools import setup

from papis import __version__
import re

def get_requirements(reqs="requirements.txt"):
    reqs = [
        line
        for line in open(reqs).read().split("\n")[0:-1]
        if not re.match(r"git\+", line)
    ]
    return reqs


setup(
    name='papis',
    version=__version__,
    maintainer='Alejandro Gallo',
    maintainer_email='aamsgallo@gmail.com',
    license='GPLv3',
    url='https://github.com/alejandrogallo/papis',
    install_requires=get_requirements(),
    dependency_links=[
        "http://github.com/alejandrogallo/python-rofi/tarball/master"
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
    packages=[
        "papis",
        "papis.commands",
        "papis.downloaders"
    ],
    test_suite="papis.tests",
    entry_points=dict(
        console_scripts=[
            'papis=papis.main:main'
        ]
    ),
    platforms=['linux'],
)
