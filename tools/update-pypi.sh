#! /usr/bin/env bash
set -ex

DIST_DIR=dist


rm -rf distenv
virtualenv -p python3.7 distenv
source ./distenv/bin/activate
pip install .
pip install .[develop]

echo "Updating man pages"
rm -rf doc/build/
make doc-man ENV=distenv

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
