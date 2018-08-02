#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging


logger = logging.getLogger("papis")
if "--debug" in sys.argv:
    log_format = '%(relativeCreated)d-'
    log_format += '%(levelname)s:%(name)s:%(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format)
    sys.argv.pop(sys.argv.index("--debug"))
    logger.debug("DEBUG MODE FOR DEVELOPERS ON")


import papis.commands.default
logger.debug("Imported commands")


def main():
    papis.commands.default.run()
