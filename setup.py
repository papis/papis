# -*- coding: utf-8 -*-
#
# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too

from __future__ import print_function

from setuptools import setup

import papis
import re


setup(
    name='papis',
    version=papis.__version__,
    maintainer='Alejandro Gallo',
    maintainer_email='aamsgallo@gmail.com',
    author=papis.__author__,
    author_email=papis.__email__,
    license=papis.__license__,
    url='https://github.com/alejandrogallo/papis',
    install_requires=[
        "requests>=2.11.1",
        "argcomplete>=1.8.2",
        "arxiv2bib>=1.0.7",
        "PyYAML>=3.12",
        "pdfminer2>=20151206",
        "chardet>=3.0.2",
        "beautifulsoup4>=4.4.1",
        "vobject>=0.9.4.1",
        "python-rofi",
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities',
    ],
    dependency_links=[
        "http://github.com/alejandrogallo/python-rofi/tarball/master"
    ],
    extras_require=dict(
        # List additional groups of dependencies here (e.g. development
        # dependencies). You can install these using the following syntax,
        # for example:
        # $ pip install -e .[develop]
        develop=[
            "sphinx",
            'sphinx-argparse',
        ]
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
        "papis.tk",
        "papis.commands",
        "papis.downloaders",
    ],
    test_suite="papis.tests",
    entry_points=dict(
        console_scripts=[
            'papis=papis.main:main'
        ]
    ),
    platforms=['linux', 'OSX'],
)
