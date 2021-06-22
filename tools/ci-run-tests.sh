#!/usr/bin/env bash

python -m pytest papis/ tests/ --cov=papis
mypy papis
flake8 papis
