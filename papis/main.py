#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging

import papis.commands
import papis.utils
import papis.config


logger = logging.getLogger("papis")


def main():
    papis.commands.init()
    papis.commands.main()


if sys.version_info < (3, 2):
    raise Exception("This script must use python 3.2 or greater")

if __name__ == "__main__":
    main()

# vim:set et sw=4 ts=4 ft=python:
