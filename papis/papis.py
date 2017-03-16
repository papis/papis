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

import re
import sys
import shutil
import requests
import tempfile
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


def getUrlService(url):
    """TODO: Docstring for getUrlService.

    :url: TODO
    :returns: TODO

    """
    m = re.match(r".*arxiv.org.*", url)
    if m:  # Arxiv
        logger.debug("Arxiv recognised")
        return "arxiv"
    return ""


def add_from_arxiv(url):
    """TODO: Docstring for add_from_arxiv.
    :url: TODO
    :returns: TODO
    """
    data = {}
    filePath = tempfile.mktemp()+".pdf"
    m = re.match(r".*arxiv.org/abs/(.*)", url)
    if m:
        p_id = m.group(1)
        logger.debug("Arxiv id = '%s'" % p_id)
    else:
        print("Arxiv url fromat not recognised, no document id found")
        sys.exit(1)
    infoUrl = \
        "http://export.arxiv.org/api/query?\
search_query=%s&start=0&max_results=1" % p_id
    pdfUrl = "https://arxiv.org/pdf/%s.pdf" % p_id
    logger.debug("Pdf url  = '%s'" % pdfUrl)
    logger.debug("Info url = '%s'" % infoUrl)
    response = requests.get(pdfUrl, stream=True)
    if response:  # Download pdf
        fd = open(filePath, "wb")
        # fd.write(response.raw)
        shutil.copyfileobj(response.raw, fd)
        logger.debug("Pdf saved in %s" % filePath)
        fd.close()
    return (filePath, data)


def main():
    config = Configuration()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Simple documents administration program"
        )

    SUBPARSER_HELP = "For further information for every \
command, type in 'papis <command> -h'"
    subparsers = parser.add_subparsers(
        help=SUBPARSER_HELP,
        metavar="command",
        dest="command"
        )
    parser.add_argument("-v",
                        "--verbose",
                        help="Make the output verbose",
                        default=False,
                        action="store_true"
                        )
    parser.add_argument("-l", "--lib",
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
            default="WARNING"
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
