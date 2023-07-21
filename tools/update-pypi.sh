#! /usr/bin/env bash
set -ex

DIST_DIR=dist
DIST_ENV=distenv

# create a virtual environment for the build
rm -rf "$DIST_ENV"
python -m venv --system-site-packages "$DIST_ENV"
source "$DIST_ENV/bin/activate"

# install build dependencies
python -m pip install --upgrade pip hatchling wheel build twine
python -m pip install .
python -m pip install .[docs]

# build package
echo 'Updating man pages'
rm -rf doc/build/
make -C doc man ENV="$DIST_ENV"

rm -rf ${DIST_DIR}
rm -rf doc/build/man/_static/
python -m build --sdist --skip-dependency-check --no-isolation .

# upload to pypi
read -p 'Do you want to push to PyPI? (y/N)' -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  twine upload ${DIST_DIR}/*.tar.gz
fi
REPLY= # unset REPLY after using it
