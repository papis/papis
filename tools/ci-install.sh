#!/usr/bin/env bash

pip install setuptools
pip install flake8
pip install python-coveralls
pip install types-requests types-PyYAML types-contextvars
pip install -e .[develop]
pip install -e .[optional]
