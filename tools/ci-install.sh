#!/usr/bin/env bash

set -o errexit -o noglob -o pipefail

python -m pip install --upgrade pip setuptools wheel
python -m pip install --editable '.[develop,optional]'
