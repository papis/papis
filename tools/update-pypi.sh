#! /usr/bin/env bash

DIST_DIR=dist

echo "Updating man pages"
make -C doc man ENV=${ENV}
make bash-autocomplete ENV=${ENV}

rm -rf ${DIST_DIR}
python3 setup.py sdist

read -p "Do you want to push? (y/N)" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  #echo "Uploading to test server"
  #twine upload -r test ${DIST_DIR}/*.tar.gz
  twine upload ${DIST_DIR}/*.tar.gz
fi
REPLY= # unset REPLY after using it
