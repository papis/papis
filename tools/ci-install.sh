#!/usr/bin/env bash

set -o errexit -o noglob -o pipefail

# NOTE: setuptools is needed as a runtime dependency of isbnlib
python -m pip install --upgrade setuptools
python -m pip install --upgrade pip hatchling wheel
python -m pip install --editable '.[develop,docs,optional]'
