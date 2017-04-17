#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# Simple document management program
# Copyright © 2016 Alejandro Gallo

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#  Import modules {{{1  #
#########################

import sys
import logging
import argparse
import argcomplete

from .config import Configuration
import papis.commands

logger = logging.getLogger("papis")

if sys.version_info < (3, 0):
    raise Exception("This script must use python 3.0 or greater")
    sys.exit(1)


#  Utility functions {{{1  #
############################


def main():
    config = Configuration()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Simple documents administration program"
        )

    SUBPARSER_HELP = "For further information for every "\
                     "command, type in 'papis <command> -h'"
    subparsers = parser.add_subparsers(
        help=SUBPARSER_HELP,
        metavar="command",
        dest="command"
        )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Make the output verbose (equivalent to --log DEBUG)",
        default=False,
        action="store_true"
    )
    parser.add_argument(
        "-l",
        "--lib",
        help="Choose a documents library, default general",
        default=config["settings"]["default"] or "papers",
        action="store"
    )
    parser.add_argument(
        "--log",
        help="Logging level",
        choices=[
            "INFO",
            "DEBUG",
            "WARNING",
            "ERROR",
            "CRITICAL"
            ],
        action="store",
        default="INFO"
    )

    subcommands = papis.commands.init(subparsers)

    # autocompletion
    argcomplete.autocomplete(parser)
    # Parse arguments
    args = parser.parse_args()

    if args.verbose:
        args.log = "DEBUG"
    logging.basicConfig(level=getattr(logging, args.log))

    if args.lib not in config.keys():
        logger.error("Library '%s' does not seem to exist" % args.lib)
        sys.exit(1)

    if args.command:
        if args.command in subcommands.keys():
            subcommands[args.command].main(config, args)
# vim:set et sw=4 ts=4 ft=python:
