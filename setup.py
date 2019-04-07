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

import glob
from setuptools import setup, find_packages
import papis

with open('README.rst') as fd:
    long_description = fd.read()

included_packages = ['papis'] + ['papis.' + p for p in find_packages('papis')]

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
        "requests>=2.11.1",
        "filetype>=1.0.1",
        "pyparsing>=2.2.0",
        "configparser>=3.0.0",
        "arxiv2bib>=1.0.7",
        "PyYAML>=3.12",
        "chardet>=3.0.2",
        "beautifulsoup4>=4.4.1",
        "colorama>=0.2",
        "bibtexparser>=0.6.2",
        "pylibgen>=1.3.0",
        "click>=7.0.0",
        "python-slugify>=1.2.6",
        "habanero>=0.6.0",
        "isbnlib>=3.9.1,<4.0.0",
        "prompt_toolkit>=2.0.5",
        "tqdm>=4.1",
        "pygments>=2.2.0",
        "stevedore>=1.30",
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
            "Jinja2>=2.10",
            "Whoosh>=2.7.4",
        ],
        develop=[
            "sphinx",
            'sphinx-click',
            'sphinx_rtd_theme',
            'pytest',
            'pytest-cov==2.5.0',
        ]
    ),
    description='Powerful and highly extensible command-line based document '
                'and bibliography manager',
    long_description=long_description,
    keywords=[
        'document', 'crossref', 'libgen', 'scihub', 'physics', 'mathematics',
        'books', 'papers', 'science', 'research',
        'bibtex', 'latex', 'command-line', 'tui', 'biblatex', 'pubmed', 'ieee',
        'reference manager', 'mendeley', 'zotero', 'elsevier',
        'cli', 'biliography', 'datasheets'
    ],
    package_data=dict(
        papis=[
        ],
    ),
    data_files=[

        ("share/doc/papis", [
            "README.rst",
            "CHANGELOG.md",
            "AUTHORS",
            "LICENSE.txt",
        ]),

        ("etc/bash_completion.d/", [
            "scripts/shell_completion/click/papis.sh",
        ]),

        ("share/zsh/site-functions/", [
            "scripts/shell_completion/click/zsh/_papis",
        ]),

        ("share/man/man1", glob.glob("doc/build/man/*")),

        ("share/applications", [
            "contrib/papis.desktop",
        ]),

    ],
    packages=included_packages,
    entry_points={
        'console_scripts': [
            'papis=papis.commands.default:run',
        ],
        'papis.exporter': [
            'bibtex=papis.commands.export:export_to_bibtex',
            'json=papis.commands.export:export_to_json',
            'yaml=papis.commands.export:export_to_yaml',
        ],
        'papis.picker': [
            'papis=papis.pick:papis_pick',
        ],
        'papis.command': [
            "add=papis.commands.add:cli",
            "addto=papis.commands.addto:cli",
            "browse=papis.commands.browse:cli",
            "config=papis.commands.config:cli",
            "edit=papis.commands.edit:cli",
            "explore=papis.commands.explore:cli",
            "export=papis.commands.export:cli",
            "git=papis.commands.git:cli",
            "list=papis.commands.list:cli",
            "mv=papis.commands.mv:cli",
            "open=papis.commands.open:cli",
            "rename=papis.commands.rename:cli",
            "rm=papis.commands.rm:cli",
            "run=papis.commands.run:cli",
            "update=papis.commands.update:cli",
        ],
        'papis.downloader': [
            "acs=papis.downloaders.acs:Downloader",
            "annualreviews=papis.downloaders.annualreviews:Downloader",
            "aps=papis.downloaders.aps:Downloader",
            "frontiersin=papis.downloaders.frontiersin:Downloader",
            "get=papis.downloaders.get:Downloader",
            "hal=papis.downloaders.hal:Downloader",
            "ieee=papis.downloaders.ieee:Downloader",
            "iopscience=papis.downloaders.iopscience:Downloader",
            "scitationaip=papis.downloaders.scitationaip:Downloader",
            "thesesfr=papis.downloaders.thesesfr:Downloader",
            "worldscientific=papis.downloaders.worldscientific:Downloader",
            "fallback=papis.downloaders.fallback:Downloader",
            "libgen=papis.downloaders.libgen:Downloader",
            "arxiv=papis.arxiv:Downloader",
        ],
        'papis.explorer': [
            "arxiv=papis.arxiv:explorer",
            "libgen=papis.libgen:explorer",
            "crossref=papis.crossref:explorer",
            "dissemin=papis.dissemin:explorer",
            "base=papis.base:explorer",
            "export=papis.commands.export:explorer",
            "isbn=papis.isbn:explorer",
            "isbnplus=papis.isbnplus:explorer",
            "yaml=papis.yaml:explorer",
            "json=papis.json:explorer",
            "bibtex=papis.bibtex:explorer",
        ]
    },
    platforms=['linux', 'osx'],
)
