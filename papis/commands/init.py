r"""
This command initializes a papis library interactively.

.. warning::

    The command will modify your configuration file, if it exists. Unfortunately,
    :mod:`configparser` does not preserve whitespace or comments when reading
    and writing a file, so these will be lost.

Examples
^^^^^^^^

- To create a new library at a given directory, just run

    .. code:: sh

        papis init /path/to/my/library

  and answer the questions interactively.

- To create a library in the current directory, just run

    .. code:: sh

        papis init

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.init:cli
    :prog: papis init
"""

from typing import NamedTuple, Optional
import os

import click

import papis.utils
import papis.config
import papis.tui.utils
import papis.logging

logger = papis.logging.get_logger(__name__)


class Prompt(NamedTuple):
    #: The name of the configuration option being suggested, e.g. ``opentool``.
    name: str
    #: A help message (in the form of a question) that describes the option.
    message: str


INIT_PROMPTS = [
    Prompt("opentool",
           "Which program should be used to open files?"),
    Prompt("editor",
           "Which program should be used when editing documents?"),
    Prompt("use-git",
           "Should papis automatically commit changes to a git repository?"),
    Prompt("notes-name",
           "What name should document attached note files have?"),
    Prompt("database-backend",
           "What database backend do you want to use?"),
    Prompt("bibtex-unicode",
           "Do you want to allow unicode in an exported BibTeX entries?"),
    Prompt("ref-format",
           "How would you like the reference string for a document be built?"),
    Prompt("multiple-authors-format",
           "What format should newly added document author lists have?"),
    Prompt("citations-file-name",
           "What name should document attached citation files have?"),
]


@click.command("init")
@click.help_option("--help", "-h")
@click.argument(
    "dir_path",
    required=False,
    type=click.Path(),
    default=None,
    metavar="<LIBRARY DIRECTORY>",
    nargs=1,
)
def cli(dir_path: Optional[str]) -> None:
    """Initialize a papis library"""

    config = papis.config.get_configuration()
    defaults = papis.config.get_default_settings()
    config_file = papis.config.get_config_file()

    if os.path.exists(config_file):
        logger.warning(
            "Config file %s already exists,"
            " this command may change some of its contents,", config_file)
        if not papis.tui.utils.confirm("Do you want to continue?"):
            return

    logger.info("Config file %s", config_file)

    library_name = papis.tui.utils.prompt(
        "Name of the library: ",
        default="papers" if dir_path is None else os.path.basename(dir_path))
    if library_name not in config:
        config[library_name] = {}
    local = config[library_name]
    glob = config[papis.config.get_general_settings_name()]

    library_path = papis.tui.utils.prompt(
        "Path of the library: ",
        default=local.get("dir",
                          os.getcwd() if dir_path is None else dir_path))

    if papis.tui.utils.confirm(
            "Make '{}' the default library?".format(library_name)):
        glob["default-library"] = library_name

    local["dir"] = library_path

    for setting, help_string in INIT_PROMPTS:
        local[setting] = papis.tui.utils.prompt(
            "{}: ".format(setting),
            default=local.get(
                setting,
                str(defaults[papis.config.get_general_settings_name()]
                    [setting])),
            bottom_toolbar=help_string)

    if papis.tui.utils.confirm("Do you want to save?"):
        with open(config_file, "w") as configfile:
            config.write(configfile)
    else:
        logger.info("exiting without saving")

    logger.info("checkout more information in "
                "https://papis.readthedocs.io/en/latest/configuration.html")
