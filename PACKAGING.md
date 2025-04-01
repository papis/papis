Guidelines for Packaging
========================

These are some loose notes about packaging Papis meant to highlight the different
components that are available and not to require a particular format.

Version Numbering
-----------------

The versioning scheme generally follows semantic versioning. That is, we
have three numbers, `A.B.C`, where:

* `A` changes on a rewrite or other major changes in the library or command-line.
* `B` changes when major configuration incompatibilities occur or major features
  are added.
* `C` changes with each release (bug fixes).

Dependencies
------------

See `pyproject.toml` for a complete list of Python dependencies and minimum versions.
Some optional dependencies are required for various Papis plugins

* `Jinja2` is required for the `jinja` formatter, alternative to the default `python`
  formatter.
* `Whoosh` is required for the `whoosh` cache database, alternative to the default
  `papis` database based on `pickle`.
* `citeproc-py` is required for the `csl` exporter, which allows exporting through
  the popular CSL (Citation Style Language) to styles like APA or MLA.
* `chardet` is used by `beautifulsoup4` when parsing webpages to improve character
  detection. This is recommended when making heavy use of Papis downloaders and
  importers.
* `markdownify` is used by the `zenodo` importer to clean up some of the project
  descriptions. By default, the raw HTML is kept as is and will appear in the
  document abstract or other such fields.

We also have some additional optional non-Python dependencies:

* `git`: The Git executable is required for the `papis git` command and other
  Git integration in various commands.

Wheels
------

Papis uses the standard `pyproject.toml`-based format and `hatchling` as a
build backend. Wheels can be generated using
```
python -m build --wheel --skip-dependency-check .
```

A source distribution (*sdist*) can be build together with the wheel using just
```
python -m build --skip-dependency-check .
```

Man pages
---------

Papis documentation uses Sphinx, which can also generate man pages. By default,
we create man pages for all the standard `papis` commands and some general
documentation for the configuration file. These can be generated using
```
make -C doc man
```

The resulting man pages can then be found in `doc/build/man` and should be installed
in appropriate locations.

Shell completions
-----------------

Papis uses `click` for its command-line parsing. To generate completions, use
```
_PAPIS_COMPLETE=bash_source papis
_PAPIS_COMPLETE=fish_source papis
_PAPIS_COMPLETE=zsh_source papis
```

Note that the generated completion files are not static and can pick up any
custom `Papis` commands and plugins even after installation.

Desktop file
------------

There is a desktop file in `contrib/papis.desktop`.
