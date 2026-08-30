#!/usr/bin/env bash

EXIT_STATUS=0

ruff check || EXIT_STATUS=$?
ty check || EXIT_STATUS=$?

exit $EXIT_STATUS
