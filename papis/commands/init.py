r"""
This command initializes a papis library interactively.

Go to the directory where you want to have your papers

::

        mkdir -p ~/Documents/papers
        cd ~/Documents/papers

::

        papis init

and answer the questions.
"""

from typing import List, Optional
import os

import click

import papis.pick
import papis.cli
import papis.utils
import papis.config
import papis.document
import papis.database
import papis.tui
import papis.logging

logger = papis.logging.get_logger(__name__)

INIT_PROMPTS = ["opentool", "editor", "use-git", "notes-name"]


@click.command("init")
@click.help_option("--help", "-h")
def cli() -> None:
    """Initialize a papis library"""

    config = papis.config.get_configuration()
    defaults = papis.config.get_default_settings()
    config_file = papis.config.get_config_file()

    if os.path.exists(config_file):
        logger.warning(
            "Config file %s already exists,"
            " this command may change some of its contents,", config_file)
        if not papis.tui.utils.confirm("Do you want to continue?"):
            return 1

    logger.info("Config file %s", config_file)

    library_name = papis.tui.utils.prompt("Name of the library: ",
                                          default="papers")
    if library_name not in config:
        config[library_name] = {}
    local = config[library_name]
    glob = config[papis.config.get_general_settings_name()]

    library_path = papis.tui.utils.prompt("Path of the library: ",
                                          default=local.get(
                                              "dir", os.getcwd()))

    if papis.tui.utils.confirm(
            "Make '{}' the default library?".format(library_name)):
        glob["default-library"] = library_name

    local["dir"] = library_path

    for setting in INIT_PROMPTS:
        local[setting] = papis.tui.utils.prompt(
            "{}: ".format(setting),
            default=local.get(
                setting,
                str(defaults[papis.config.get_general_settings_name()]
                    [setting])))

    if papis.tui.utils.confirm("Do you want to save?"):
        with open(config_file, 'w') as configfile:
            config.write(configfile)
