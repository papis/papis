#!/usr/bin/env bash

set -o errexit -o noglob -o pipefail

uv pip install --upgrade pip hatchling wheel
uv pip install --editable '.[develop,docs,optional]'
