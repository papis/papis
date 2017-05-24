#! /usr/bin/env python3
# -*- coding: utf-8 -*-

#  Import modules {{{1  #
#########################

import sys
import logging

import papis.commands
import papis.utils
import papis.config

logger = logging.getLogger("papis")

if sys.version_info < (3, 0):
    raise Exception("This script must use python 3.0 or greater")
    sys.exit(1)


#  Utility functions {{{1  #
############################


def main():
    papis.commands.init()
    papis.commands.main()


# vim:set et sw=4 ts=4 ft=python:
