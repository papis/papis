#! /usr/bin/env bash
set -ex

DIST_DIR=dist


# install build dependencies
python -m pip install --upgrade pip hatchling wheel build twine
python -m pip install .
python -m pip install .[docs]

echo "Updating man pages"
rm -rf doc/build/
make -C doc man ENV=distenv

rm -rf ${DIST_DIR}
rm -rf doc/build/man/_static/
python3 setup.py sdist

pip install twine
read -p "Do you want to push? (y/N)" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  twine upload ${DIST_DIR}/*.tar.gz
fi
REPLY= # unset REPLY after using it
