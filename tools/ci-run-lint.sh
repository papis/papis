#!/usr/bin/env bash

EXIT_STATUS=0

python -m flake8 papis tests examples || EXIT_STATUS=$?
python -m mypy papis || EXIT_STATUS=$?

exit $EXIT_STATUS
