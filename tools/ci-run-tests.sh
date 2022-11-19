#!/usr/bin/env bash

PYTHON_MINOR_VERSION=$(python -c 'import sys; print(sys.version_info.minor)')
EXIT_STATUS=0

python -m pytest papis/ tests/ --cov=papis || EXIT_STATUS=$?
python -m flake8 papis || EXIT_STATUS=$?
if (( "$PYTHON_MINOR_VERSION" > 6)); then
    python -m mypy --show-error-codes papis || EXIT_STATUS=$?
fi

exit $EXIT_STATUS
