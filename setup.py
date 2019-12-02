# -*- coding: utf-8 -*-
#
# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too

import sys
import glob
from setuptools import setup, find_packages
import papis

with open('README.rst') as fd:
    long_description = fd.read()

if sys.platform == 'win32':
    data_files = []
else:
    data_files = [

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

    ]

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
        "click>=7.0.0",
        "habanero>=0.6.0",
        "isbnlib>=3.9.1",
        "prompt_toolkit>=2.0.5",
        "tqdm>=4.1",
        "pygments>=2.2.0",
        "stevedore>=1.30",
        "python-doi>=0.1.1",
        # for python 3.4
        "lxml<=4.3.5 ; python_version<='3.5'",
        "lxml>=4.3.5 ; python_version>'3.5'",
        "python-slugify>=1.2.6,<4 ; python_version<='3.4'",
        "python-slugify>=1.2.6 ; python_version>'3.4'",
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
            "Whoosh>=2.7.4",
        ],
        develop=[
            'sphinx-click',
            'sphinx_rtd_theme',
            'pytest',
            'pytest-cov==2.5.0',
        ]
    ),
    description=(
        'Powerful and highly extensible command-line based document '
        'and bibliography manager'
    ),
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
    data_files=data_files,
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
        'papis.importer': [
            'bibtex=papis.bibtex:Importer',
            'yaml=papis.yaml:Importer',
            'doi=papis.crossref:Importer',
            'crossref=papis.crossref:FromCrossrefImporter',
            'pdf2doi=papis.crossref:DoiFromPdfImporter',
            # 'url=papis.downloaders:Importer',
            'arxiv=papis.arxiv:Importer',
            'pdf2arxivid=papis.arxiv:ArxividFromPdfImporter',
            'pmid=papis.pubmed:Importer',
            'lib=papis.commands.add:FromLibImporter',
            'folder=papis.commands.add:FromFolderImporter',
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
            "bibtex=papis.commands.bibtex:cli",
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
            "doi=papis.crossref:Downloader",
            "ieee=papis.downloaders.ieee:Downloader",
            "sciencedirect=papis.downloaders.sciencedirect:Downloader",
            "tandfonline=papis.downloaders.tandfonline:Downloader",
            "springer=papis.downloaders.springer:Downloader",
            "iopscience=papis.downloaders.iopscience:Downloader",
            "scitationaip=papis.downloaders.scitationaip:Downloader",
            "thesesfr=papis.downloaders.thesesfr:Downloader",
            "worldscientific=papis.downloaders.worldscientific:Downloader",
            "fallback=papis.downloaders.fallback:Downloader",
            "arxiv=papis.arxiv:Downloader",
        ],
        'papis.explorer': [
            "lib=papis.commands.explore:lib",
            "citations=papis.commands.explore:citations",
            "cmd=papis.commands.explore:cmd",
            "pick=papis.commands.explore:pick",
            "arxiv=papis.arxiv:explorer",
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
