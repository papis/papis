#!/usr/bin/env bash

python -m pip install --upgrade pip setuptools
python -m pip install flake8 flake8-quotes flake8-bugbear
python -m pip install \
    "pep8-naming; python_version>='3.6'" \
    "pep8-naming<0.13.0; python_version<'3.6'"
python -m pip install python-coveralls
python -m pip install types-requests types-PyYAML types-contextvars
python -m pip install -e .[develop]
python -m pip install -e .[optional]
