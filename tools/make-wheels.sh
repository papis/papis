#! /usr/bin/env bash
set -ex

DIST_DIR=dist
DIST_ENV=.venv

# create a virtual environment for the build
rm -rf "$DIST_ENV"
python -m venv --system-site-packages "$DIST_ENV"
source "$DIST_ENV/bin/activate"

# install build dependencies
python -m pip install --upgrade pip hatchling wheel build
python -m pip install .
python -m pip install .[docs]

# build package
echo 'Updating man pages'
rm -rf doc/build/
make -C doc man ENV="$DIST_ENV"

rm -rf ${DIST_DIR}
rm -rf doc/build/man/_static/
python -m build --skip-dependency-check .
