#! /usr/bin/env python3
# -*- coding: utf-8 -*-

#  Import modules {{{1  #
#########################

import sys
import logging
import argcomplete

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
    config = papis.config.get_configuration()

    parser = papis.commands.get_default_parser()
    # subparser = papis.commands.get_subparser()
    subcommands = papis.commands.init()

    # autocompletion
    argcomplete.autocomplete(parser)
    # Parse arguments
    args = parser.parse_args()
    papis.utils.set_args(args)

# vim:set et sw=4 ts=4 ft=python:
