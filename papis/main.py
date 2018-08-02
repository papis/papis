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

import click
import papis.cli

@click.group(
    cls=papis.cli.MultiCommand,
    invoke_without_command=True
)
@click.help_option('--help', '-h')
@click.version_option(version=papis.__version__)
@click.option(
    "-v",
    "--verbose",
    help="Make the output verbose (equivalent to --log DEBUG)",
    default=False,
    is_flag=True
)
@click.option(
    "-l",
    "--lib",
    help="Choose a library name or library path (unamed library)",
    default=lambda: papis.config.get("default-library")
)
@click.option(
    "-c",
    "--config",
    help="Configuration file to use",
    default=None,
)
@click.option(
    "--log",
    help="Logging level",
    type=click.Choice([ "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL" ]),
    default="INFO"
)
@click.option(
    "--picktool",
    help="Override picktool",
    default=""
)
@click.option(
    "--pick-lib",
    help="Pick library to use",
    default=False,
    is_flag=True
)
@click.option(
    "--clear-cache", "--cc",
    help="Clear cache of the library used",
    default=False,
    is_flag=True
)
@click.option(
    "-j", "--cores",
    help="Number of cores to run some multicore functionality",
    type=int,
    default=__import__("multiprocessing").cpu_count(),
)
@click.option(
    "--set",
    type=(str,str),
    multiple=True,
    help="Set key value, e.g., "
         "--set info-name information.yaml  --set opentool evince",
)
def main(
        verbose,
        config,
        lib,
        log,
        picktool,
        pick_lib,
        cc,
        cores,
        set
    ):
    papis.commands.default.run(
        verbose,
        config,
        lib,
        log,
        picktool,
        pick_lib,
        cc,
        cores,
        set
    )
