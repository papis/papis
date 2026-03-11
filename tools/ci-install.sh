#!/usr/bin/env bash

set -o errexit -o noglob -o pipefail

python -m pip install --upgrade pip hatchling wheel
python -m pip install --editable '.[develop,docs,optional]'

# NOTE: setuptools is needed as a runtime dependency of isbnlib
python -m pip install --upgrade 'setuptools<82.0.0'
