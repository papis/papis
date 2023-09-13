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
from typing import Optional  # noqa: F401
import os

import click

import papis.utils
import papis.config
import papis.tui.utils
import papis.logging

logger = papis.logging.get_logger(__name__)

INIT_PROMPTS = [
    {
        "key": "opentool",
        "help": "Which program should be used to open files? e.g. evince"
    },
    {
        "key": "editor",
        "help": "Which program should be called when editing info.yaml files?"
    },
    {
        "key": "use-git",
        "help":
        "Use git in some papis commands to issue commits automatically?"
    },
    {
        "key": "notes-name",
        "help": "The name of the file for notes."
    },
    {
        "key": "database-backend",
        "help": "You can choose between different kinds of databases."
    },
    {
        "key": "bibtex-unicode",
        "help": "Do you want to allow unicode in an exported bibtex?"
    },
    {
        "key":
        "ref-format",
        "help":
        "When adding a new document, "
        "how would you like the reference string be built?"
    },
    {
        "key": "multiple-authors-format",
        "help": ""
    },
    {
        "key": "citations-file-name",
        "help": ""
    },
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

    for setting_dict in INIT_PROMPTS:
        setting, help_string = setting_dict.values()
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
