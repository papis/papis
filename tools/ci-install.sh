#!/usr/bin/env bash

python -m pip install --upgrade pip setuptools
python -m pip install flake8
python -m pip install python-coveralls
python -m pip install types-requests types-PyYAML types-contextvars
python -m pip install -e .[develop]
python -m pip install -e .[optional]
