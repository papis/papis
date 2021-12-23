#!/usr/bin/env bash

python -m pytest papis/ tests/ --cov=papis
python -m mypy papis
python -m flake8 papis
