#
# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too

import os
import sys
import glob

from setuptools import setup, find_packages

import papis

with open("README.rst") as fd:
    long_description = fd.read()

if sys.platform == "win32":
    data_files = []
else:
    # NOTE: see the documentation for 'bash-completion' at
    #   https://github.com/scop/bash-completion/blob/master/README.md#faq
    bash_completion_dir = os.environ.get(
        "PAPIS_BASH_COMPLETION_DIR", "share/bash-completion/completions")
    # NOTE: see the documentation for 'fish' at
    #   https://fishshell.com/docs/current/completions.html#where-to-put-completions
    fish_completion_dir = os.environ.get(
        "PAPIS_FISH_COMPLETION_DIR", "share/fish/vendor_completions.d")
    # NOTE: 'site-functions' is included by default since zsh 5.0.7, see
    #   https://zsh.sourceforge.io/releases.html
    zsh_completion_dir = os.environ.get(
        "PAPIS_ZSH_COMPLETION_DIR", "share/zsh/site-functions")

    data_files = [
        ("share/doc/papis", [
            "README.rst",
            "CHANGELOG.md",
            "AUTHORS",
            "LICENSE",
        ]),

        (bash_completion_dir, ["scripts/shell_completion/click/bash/papis.bash"]),
        (fish_completion_dir, ["scripts/shell_completion/click/fish/papis.fish"]),
        (zsh_completion_dir, ["scripts/shell_completion/click/zsh/_papis"]),

        ("share/man/man1", glob.glob("doc/build/man/*")),
        ("share/applications", ["contrib/papis.desktop"]),
    ]

included_packages = ["papis"] + ["papis." + p for p in find_packages("papis")]

setup(
    name="papis",
    version=papis.__version__,
    maintainer="Alejandro Gallo",
    maintainer_email="aamsgallo@gmail.com",
    author=papis.__author__,
    author_email=papis.__email__,
    license=papis.__license__,
    url="https://github.com/papis/papis",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: Microsoft",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
    ],
    install_requires=[
        "PyYAML>=3.12",
        "arxiv>=1.0.0",
        "beautifulsoup4>=4.4.1",
        "bibtexparser>=1.4,<2",
        "chardet>=3.0.2",
        "click>=7.0.0",
        "colorama>=0.2",
        "dominate",
        "filetype>=1.0.1",
        "habanero>=0.6.0",
        "isbnlib>=3.9.1",
        "lxml>=4.3.5",
        "prompt_toolkit>=3.0.0",
        "pygments>=2.2.0",
        "pyparsing>=2.2.0",
        "python-doi>=0.1.1",
        "python-slugify>=1.2.6",
        "requests>=2.11.1",
        "stevedore>=1.30",
        "tqdm>=4.1",
    ],
    python_requires=">=3.8",
    extras_require={
        # List additional groups of dependencies here (e.g. development
        # dependencies). You can install these using the following syntax,
        # for example:
        # $ pip install -e .[develop]
        "optional": [
            "Jinja2>=3.0.0",
            "Whoosh>=2.7.4",
        ],
        "develop": [
            "flake8",
            "flake8-bugbear",
            "flake8-quotes",
            "mypy>=0.7",
            "pep8-naming",
            "pylint",
            "pytest",
            "pytest-cov",
            "python-coveralls",
            "python-lsp-server",
            "sphinx-click",
            "sphinx-rtd-theme>=1",
            "types-PyYAML",
            "types-Pygments",
            "types-beautifulsoup4",
            "types-docutils",
            "types-python-slugify",
            "types-requests",
            "types-tqdm",
        ],
    },
    description=(
        "Powerful and highly extensible command-line based document "
        "and bibliography manager"
    ),
    long_description=long_description,
    keywords=[
        "biblatex",
        "bibtex",
        "biliography",
        "books",
        "cli",
        "command-line",
        "crossref",
        "datasheets",
        "document",
        "elsevier",
        "ieee",
        "latex",
        "libgen",
        "mathematics",
        "mendeley",
        "papers",
        "physics",
        "pubmed",
        "reference manager",
        "research",
        "science",
        "scihub",
        "tui",
        "zotero",
    ],
    package_data={
        "papis": ["py.typed"],
    },
    data_files=data_files,
    packages=included_packages,
    entry_points={
        "console_scripts": [
            "papis=papis.commands.default:run",
        ],
        "pytest11": [
            "papis_testing=papis.testing",
        ],
        "papis.hook.on_edit_done": [
        ],
        "papis.exporter": [
            "bibtex=papis.bibtex:exporter",
            "json=papis.json:exporter",
            "typst=papis.hayagriva:exporter",
            "yaml=papis.yaml:exporter",
        ],
        "papis.importer": [
            "arxiv=papis.arxiv:Importer",
            "bibtex=papis.bibtex:Importer",
            "crossref=papis.crossref:FromCrossrefImporter",
            "dblp=papis.dblp:Importer",
            "doi=papis.crossref:Importer",
            "folder=papis.commands.add:FromFolderImporter",
            "isbn=papis.isbn:Importer",
            "lib=papis.commands.add:FromLibImporter",
            "pdf2arxivid=papis.arxiv:ArxividFromPdfImporter",
            "pdf2doi=papis.crossref:DoiFromPdfImporter",
            "pmid=papis.pubmed:Importer",
            "yaml=papis.yaml:Importer",
        ],
        "papis.picker": [
            "fzf=papis.fzf:Picker",
            "papis=papis.tui.picker:Picker",
        ],
        "papis.format": [
            "jinja2=papis.format:Jinja2Formatter",
            "python=papis.format:PythonFormatter",
        ],
        "papis.command": [
            "add=papis.commands.add:cli",
            "addto=papis.commands.addto:cli",
            "bibtex=papis.commands.bibtex:cli",
            "browse=papis.commands.browse:cli",
            "citations=papis.commands.citations:cli",
            "config=papis.commands.config:cli",
            "doctor=papis.commands.doctor:cli",
            "edit=papis.commands.edit:cli",
            "exec=papis.commands.exec:cli",
            "explore=papis.commands.explore:cli",
            "export=papis.commands.export:cli",
            "git=papis.commands.git:cli",
            "list=papis.commands.list:cli",
            "merge=papis.commands.merge:cli",
            "mv=papis.commands.mv:cli",
            "open=papis.commands.open:cli",
            "rename=papis.commands.rename:cli",
            "rm=papis.commands.rm:cli",
            "run=papis.commands.run:cli",
            "serve=papis.commands.serve:cli",
            "tag=papis.commands.tag:cli",
            "update=papis.commands.update:cli",
            "cache=papis.commands.cache:cli",
            "init=papis.commands.init:cli",
        ],
        "papis.downloader": [
            "acm=papis.downloaders.acm:Downloader",
            "acs=papis.downloaders.acs:Downloader",
            "acl=papis.downloaders.acl:Downloader",
            "annualreviews=papis.downloaders.annualreviews:Downloader",
            "aps=papis.downloaders.aps:Downloader",
            "arxiv=papis.arxiv:Downloader",
            "citeseerx=papis.downloaders.citeseerx:Downloader",
            "doi=papis.crossref:Downloader",
            "fallback=papis.downloaders.fallback:Downloader",
            "frontiersin=papis.downloaders.frontiersin:Downloader",
            "get=papis.downloaders.get:Downloader",
            "hal=papis.downloaders.hal:Downloader",
            "ieee=papis.downloaders.ieee:Downloader",
            "iopscience=papis.downloaders.iopscience:Downloader",
            "projecteuclid=papis.downloaders.projecteuclid:Downloader",
            "sciencedirect=papis.downloaders.sciencedirect:Downloader",
            "scitationaip=papis.downloaders.scitationaip:Downloader",
            "springer=papis.downloaders.springer:Downloader",
            "tandfonline=papis.downloaders.tandfonline:Downloader",
            "thesesfr=papis.downloaders.thesesfr:Downloader",
            "worldscientific=papis.downloaders.worldscientific:Downloader",
            "usenix=papis.downloaders.usenix:Downloader",
        ],
        "papis.explorer": [
            "add=papis.commands.explore:add",
            "arxiv=papis.arxiv:explorer",
            "bibtex=papis.bibtex:explorer",
            "citations=papis.commands.explore:citations",
            "cmd=papis.commands.explore:cmd",
            "crossref=papis.crossref:explorer",
            "dblp=papis.dblp:explorer",
            "dissemin=papis.dissemin:explorer",
            "export=papis.commands.export:explorer",
            "isbn=papis.isbn:explorer",
            "json=papis.json:explorer",
            "lib=papis.commands.explore:lib",
            "pick=papis.commands.explore:pick",
            "yaml=papis.yaml:explorer",
        ]
    },
    platforms=["linux", "osx", "win32"],
)
