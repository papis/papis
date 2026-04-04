#! /usr/bin/env bash
set -ex

DIST_DIR=dist
DIST_ENV=.venv

# create a virtual environment for the build
rm -rf "$DIST_ENV"
python -m venv --system-site-packages "$DIST_ENV"
source "$DIST_ENV/bin/activate"

# install build dependencies
python -m pip install --upgrade pip hatchling wheel build twine
python -m pip install .
python -m pip install .[docs]

# build man pages
echo 'Updating man pages'
rm -rf doc/build/
make -C doc man ENV="$DIST_ENV"

# clean directories (so they do not show up in the sdist)
rm -rf ${DIST_DIR}
rm -rf doc/build/man/_static/

# clean README.rst so that it works on PyPI (does not support '.. raw' directives)
sed -i '1,26d' README.rst
sed -i '1s/^/Papis\n/' README.rst
sed -i '2s/^/=====\n\n/' README.rst
sed -i '4s/^/|ghbadge| |RTD| |CodeQL| |Pypi| |zenodo_badge|\n\n/' README.rst
sed -i '6s/^/Papis is a powerful and highly extensible CLI document and bibliography manager.\n/' README.rst

# build wheel
python -m build --skip-dependency-check .
twine check --strict dist/*
