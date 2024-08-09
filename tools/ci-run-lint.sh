#!/usr/bin/env bash

set -e

ruff check papis tests examples
python -m mypy papis
