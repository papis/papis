Guidelines for Packaging
========================

These are some loose notes about packing Papis meant to highlight the different
components that are available and not to require a particular format.

Dependencies
============

See `pyproject.toml` for a complete list of dependencies and minimum versions.

Wheels
======

Papis uses the standard `pyproject.toml`-based format using `hatchling` as a
build backend. Wheels can be generated using
```
python -m build --wheel --skip-dependency-check .
```

A source distribution (*sdist*) can be build together with the wheel using just
```
python -m build --skip-dependency-check .
```

Man pages
=========

Papis documentation uses Sphinx, which can also generate man pages. By default,
we create man pages for all the standard Papis commands and some general
documentation for the configuration file. These can be generated using
```
make -C doc man
```

The resulting man pages can then be found in `doc/build/man` and should be installed
in appropriate locations.

Shell completions
=================

Papis uses `click` for its command-line parsing. To generate completions, use
```
_PAPIS_COMPLETE=bash_source papis
_PAPIS_COMPLETE=fish_source papis
_PAPIS_COMPLETE=zsh_source papis
```

Note that the generated completion files are not static and can pick up any
custom Papis commands and plugins even after installation.

Desktop file
============

There is a desktop file in `contrib/papis.desktop`.
