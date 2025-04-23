#!/usr/bin/env bash

EXIT_STATUS=0

python -m flake8 papis tests examples tools || EXIT_STATUS=$?
python -m mypy papis tests examples tools || EXIT_STATUS=$?

exit $EXIT_STATUS
