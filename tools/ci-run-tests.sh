#!/usr/bin/env bash

PYTHON_MINOR_VERSION=$(python -c 'import sys; print(sys.version_info.minor)')
EXIT_STATUS=0

python -m pytest -v papis/ tests/ --cov=papis || EXIT_STATUS=$?
python -m flake8 papis tests examples || EXIT_STATUS=$?
python -m mypy --show-error-codes papis || EXIT_STATUS=$?

exit $EXIT_STATUS
