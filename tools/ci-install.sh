#!/usr/bin/env bash

set -o errexit -o noglob -o pipefail

python -m pip install --upgrade pip hatchling wheel
python -m pip install --editable '.[develop,docs,optional]'

# NOTE: setuptools is needed as a runtime dependency of isbnlib
python -m pip install --upgrade setuptools
# NOTE: sphinx>=9.1.0 uses 3.12 syntax for typing and breaks mypy on the CI
python -m pip install --upgrade 'sphinx<9.1.0'
