# -*- coding: utf-8 -*-
#
# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too

import sys

main_dependencies = [ "setuptools" ]
for dep in main_dependencies:
    try:
        __import__(dep)
    except ImportError:
        print(
            "Error: You do not have %s installed, please\n"
            "       install it. For example doing\n"
            "\n"
            "       pip3 install %s\n" % (dep, dep)
        )
        sys.exit(1)

from setuptools import setup
import papis

with open('README.rst') as fd:
    long_description = fd.read()

setup(
    name='papis',
    version=papis.__version__,
    maintainer='Alejandro Gallo',
    maintainer_email='aamsgallo@gmail.com',
    author=papis.__author__,
    author_email=papis.__email__,
    license=papis.__license__,
    url='https://github.com/papis/papis',
    install_requires=[
        "click>=6.7",
        "requests>=2.11.1",
        "pyparsing>=2.2.0",
        "configparser>=3.0.0",
        "arxiv2bib>=1.0.7",
        "PyYAML>=3.12",
        "chardet>=3.0.2",
        "beautifulsoup4>=4.4.1",
        "prompt-toolkit>=2.0.0",
        "bibtexparser>=0.6.2",
        "python-slugify==1.2.5",
        "pyparser>=1.0",
        "pylibgen>=1.3.0",
        "habanero>=0.6.0",
    ],
    python_requires='>=3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
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
    extras_require=dict(
        # List additional groups of dependencies here (e.g. development
        # dependencies). You can install these using the following syntax,
        # for example:
        # $ pip install -e .[develop]
        optional=[
            'dmenu',
            "Jinja2>=2.10",
            "Whoosh>=2.7.4",
        ],
        develop=[
            "sphinx",
            'sphinx-click',
            'sphinx_rtd_theme',
            'pytest',
            'pytest-cov',
        ]
    ),
    description='Powerful and highly extensible command-line based document '
                'and bibliography manager',
    long_description=long_description,
    keywords=[
        'document',
        'books',
        'bibtex',
        'management',
        'cli',
        'biliography'
    ],
    package_data=dict(
        papis=[
            'gui/vim/main.vim',
        ],
    ),
    data_files=[

        ("share/doc/papis/", [
            "README.rst",
            "AUTHORS",
            "LICENSE.txt",
        ]),

        # ("etc/bash_completion.d/", [
            # "scripts/shell_completion/build/bash/papis",
        # ]),

        ("share/man/man1", [
            "doc/build/man/papis.1",
            "doc/build/man/papis-config.1",
        ]),

        ("share/applications", [
            "contrib/papis.desktop",
        ]),

    ],
    packages=[
        "papis",
        "papis.gui",
        "papis.gui.vim",
        "papis.commands",
        "papis.database",
        "papis.downloaders",
    ],
    entry_points=dict(
        console_scripts=[
            'papis=papis.main:main'
        ]
    ),
    platforms=['linux', 'osx'],
)
