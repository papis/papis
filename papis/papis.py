#! /usr/bin/env python3
# -*- coding: utf-8 -*-

#  Import modules {{{1  #
#########################

import sys
import logging
import argparse
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
            subcommands[args.command].main(args)
# vim:set et sw=4 ts=4 ft=python:
