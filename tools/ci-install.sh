#!/usr/bin/env bash

set -o errexit -o noglob -o pipefail

python -m pip install --upgrade pip hatchling wheel
python -m pip install --editable '.[develop,docs,optional]'
