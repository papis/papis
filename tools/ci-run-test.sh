#!/usr/bin/env bash

set -o errexit -o noglob -o pipefail

python -m pytest papis tests
