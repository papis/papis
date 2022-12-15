#!/usr/bin/env bash

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[develop]
python -m pip install -e .[optional]
