r"""
This command initializes a Papis library interactively.

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


def _is_git_repository(path: str) -> bool:
    path = os.path.abspath(path)

    while True:
        # check if a '.git' subdirectory exists
        git_path = os.path.join(path, ".git")
        if os.path.exists(git_path):
            return True

        # check if we reached the root
        parent = os.path.dirname(path)
        if parent == path:
            break

        path = parent

    return False


@click.command("init")
@click.help_option("--help", "-h")
@click.argument(
    "dir_path",
    required=False,
    type=click.Path(file_okay=False),
    default=None,
    metavar="<LIBRARY DIRECTORY>",
    nargs=1,
)
def cli(dir_path: Optional[str]) -> None:
    """Initialize a papis library"""

    from papis.tui.utils import confirm, prompt

    config = papis.config.get_configuration()
    general_settings_name = papis.config.get_general_settings_name()
    defaults = papis.config.get_default_settings()[general_settings_name]
    config_file = papis.config.get_config_file()

    has_config_file = os.path.exists(config_file)
    if has_config_file:
        logger.warning("Config file '%s' already exists!", config_file)
        logger.warning(
            "This command may change some of its contents, e.g. whitespace and "
            "comments are not preserved.")

        if not confirm("Do you want to continue?"):
            return
    else:
        logger.info("Initializing a new config file: '%s'.", config_file)

    logger.info("Setting library location:")
    dir_path = os.getcwd() if dir_path is None else dir_path

    known_libraries = papis.config.get_libs() if has_config_file else {}
    library_name = prompt(
        "Name of the library",
        default=os.path.basename(dir_path),
        bottom_toolbar=(
            "Known libraries: '{}'".format("', '".join(known_libraries))
            if known_libraries else "No currently configured libraries")
        )

    if library_name not in config:
        config.add_section(library_name)
    local = config[library_name]
    glob = config[general_settings_name]

    library_path = prompt(
        "Path of the library",
        default=local.get("dir", dir_path),
        bottom_toolbar="Give an existing folder for the library location")

    if not os.path.exists(library_path):
        if confirm(f"Library path '{library_path}' does not exist. Create it?"):
            os.makedirs(library_path)

    default_library = (
        glob.get("default-library", defaults.get("default-library"))
        if has_config_file else None)
    if confirm(f"Make '{library_name}' the default library? "
               f"(currently '{default_library}')",
               yes=not known_libraries):
        glob["default-library"] = library_name

    local["dir"] = os.path.abspath(library_path)

    logger.info("Setting library custom options.")
    if confirm("Want to add some standard settings?", yes=False):
        for setting, help_string in INIT_PROMPTS:
            local[setting] = prompt(
                setting,
                default=str(local.get(setting, defaults.get(setting))),
                bottom_toolbar=help_string)

    papis.config.set_lib_from_name(library_name)
    use_git = papis.config.getboolean("use-git")
    if use_git and not _is_git_repository(library_path):
        if confirm(f"Library '{library_path}' is not a git repository and 'use-git' "
                   "is enabled. Would you like to initialize a git repository?"):
            papis.git.init(library_path)
            papis.git.add(library_path, ".")
            papis.git.commit(library_path, f"Initialized library '{library_name}'")

    if confirm("Do you want to save?"):
        config_folder = papis.config.get_config_folder()
        if not os.path.exists(config_folder):
            os.makedirs(config_folder)

        if not has_config_file:
            config.remove_section("papers")

        with open(config_file, "w", encoding="utf-8") as configfile:
            config.write(configfile)

        logger.info("Configuration file saved at '%s'.", config_file)

    logger.info("Check out more information about papis!")
    logger.info("   Configuration options: "
                "https://papis.readthedocs.io/en/latest/configuration.html")
    logger.info("   Library structure:     "
                "https://papis.readthedocs.io/en/latest/library_structure.html")
    logger.info("   Ask questions:         "
                "https://github.com/papis/papis/discussions")
