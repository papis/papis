"""
The ``papis`` command (without any subcommands) can be used to set configuration
options or select the library.

Examples
^^^^^^^^

- To override some configuration options, you can use the ``--set`` flag. For
  instance, if you want to override the ``editor`` used to edit files or the
  ``opentool`` used to open documents, you can just type:

    .. code:: sh

        papis --set editor gedit --set opentool firefox edit
        papis --set editor gedit --set opentool firefox open

- If you want to list the libraries and pick one before sending a database
  query to Papis, use ``--pick-lib`` as such:

    .. code:: sh

        papis --pick-lib open 'einstein relativity'

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.default:run
    :prog: papis
"""

import os
from collections.abc import Callable
from functools import cached_property
from typing import TYPE_CHECKING

import click

import papis.cli
import papis.logging

if TYPE_CHECKING:
    import cProfile

    from papis.commands import CommandPlugin

logger = papis.logging.get_logger(__name__)


class CommandPluginLoaderGroup(click.Group):

    @cached_property
    def command_plugins(self) -> dict[str, "CommandPlugin"]:
        from papis.commands import get_commands

        return get_commands()

    @cached_property
    def command_plugin_names(self) -> list[str]:
        return sorted(self.command_plugins)

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List all matched commands in the command folder and in path

        >>> group = CommandPluginLoaderGroup()
        >>> rv = group.list_commands(None)
        >>> len(rv) > 0
        True
        """
        return self.command_plugin_names

    def get_command(
            self,
            ctx: click.Context,
            name: str) -> click.Command | None:
        """Get the command to be run

        >>> group = CommandPluginLoaderGroup()
        >>> cmd = group.get_command(None, 'add')
        >>> cmd.name, cmd.help
        ('add', 'Add...')
        >>> group.get_command(None, 'this command does not exist')
        Command ... is unknown!
        """
        try:
            cmd = self.command_plugins[name]
        except KeyError:
            import difflib
            matches = list(map(
                str, difflib.get_close_matches(name, self.command_plugin_names, n=2)))

            click.echo(f"Command '{name}' is unknown!")
            if len(matches) == 1:
                # return the match if there was only one match
                click.echo(f"I suppose you meant: '{matches[0]}'")
                cmd = self.command_plugins[matches[0]]
            elif matches:
                click.echo("Did you mean '{matches}'?"
                           .format(matches="' or '".join(matches)))
                return None
            else:
                return None

        from papis.commands import load_command
        return load_command(cmd)


def generate_profile_writing_function(profiler: "cProfile.Profile",
                                      filename: str) -> Callable[[], None]:
    def _on_finish() -> None:
        profiler.disable()
        profiler.dump_stats(filename)

    return _on_finish


@click.group(
    cls=CommandPluginLoaderGroup,
    invoke_without_command=False)
@click.help_option("--help", "-h")
@click.version_option(version=papis.__version__)
@papis.cli.bool_flag(
    "-v", "--verbose",
    help="Make the output verbose (equivalent to --log DEBUG).",
    default="PAPIS_DEBUG" in os.environ)
@click.option(
    "--profile",
    help="Print profiling information into file.",
    type=click.Path(),
    default=None)
@click.option(
    "-l", "--lib",
    help="Choose a library name or library path (unnamed library).",
    type=papis.cli.LibraryParamType(),
    default=None)
@click.option(
    "-c",
    "--config",
    help="Configuration file to use.",
    type=click.Path(exists=True),
    default=None)
@papis.cli.bool_flag(
    "--pick-lib",
    help="Pick library to use.")
@click.option(
    "-s", "--set", "set_list",
    type=(str, str),
    multiple=True,
    help="Set key value, e.g., "
         "'--set info-name information.yaml --set opentool evince'.")
@click.option(
    "--color",
    type=click.Choice(["always", "auto", "no"]),
    default=os.environ.get("PAPIS_LOG_COLOR", "auto"),
    help="Prevent the output from having color.")
@click.option(
    "--log",
    help="Logging level.",
    type=click.Choice(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]),
    default=os.environ.get("PAPIS_LOG_LEVEL", "INFO"))
@click.option(
    "--logfile",
    help="File to dump the log.",
    type=str,
    default=os.environ.get("PAPIS_LOG_FILE"))
@click.option(
    "--np",
    help="Use number of processors for multicore functionalities in Papis.",
    type=str,
    default=None)
@click.pass_context
def run(ctx: click.Context,
        verbose: bool,
        profile: str,
        config: str,
        lib: str | None,
        log: str,
        logfile: str | None,
        pick_lib: bool,
        set_list: list[tuple[str, str]],
        color: str,
        np: int | None) -> None:
    import papis.config

    if np:
        os.environ["PAPIS_NP"] = str(np)

    if profile:
        import cProfile
        profiler = cProfile.Profile()
        profiler.enable()

        import atexit
        atexit.register(generate_profile_writing_function(profiler, profile))

    papis.logging.setup(log, color=color, logfile=logfile, verbose=verbose)

    # NOTE: order of the configurations is intentional based on priority
    #
    #   4. default hardcoded settings in `papis/config.py`
    #   3. global papis configuration file, e.g. `~/.config/papis/config`
    #   2. library local configuration file, e.g. `LIBDIR/.config`
    #   1. command-line arguments, e.g. `--set opentool firefox`

    # read in configuration file
    if config:
        papis.config.set_config_file(config)
        papis.config.reset_configuration()

    # read in configuration from current library
    if pick_lib:
        picked_libs = papis.pick.pick_library()
        if picked_libs:
            lib = picked_libs[0]

    if lib is None:
        # NOTE: check if the current folder is a configured library
        libdir = os.getcwd()
        config_lib_dirs = {
            path: libname
            for libname in papis.config.get_libs()
            for path in papis.config.get_lib_from_name(libname).paths
        }

        while libdir != (nextlibdir := os.path.dirname(libdir)):
            if libdir in config_lib_dirs:
                lib = config_lib_dirs[libdir]
                break

            libdir = nextlibdir

        # if the cwd does not match any library, use default library
        if lib is None:
            lib = papis.config.getstring("default-library")

    papis.config.set_lib_from_name(lib)
    library = papis.config.get_lib()

    configuration = papis.config.get_configuration()
    if library.paths:
        # Now the library should be set, let us check if there is a
        # local configuration file there, and if there is one, then
        # merge its contents
        local_config_file = papis.config.getstring("local-config-file")
        for path in library.paths:
            local_config_path = os.path.join(path, local_config_file)
            papis.config.merge_configuration_from_path(local_config_path, configuration)
    else:
        config_file = papis.config.get_config_file()
        if os.path.exists(config_file):
            logger.error(
                "Library '%s' does not have any folders attached to it. Please "
                "create and add the required paths to the configuration file.",
                library)
        elif ctx.invoked_subcommand != "init":
            logger.warning("No configuration file exists at '%s'.", config_file)
            logger.warning("Create a configuration file and define your "
                           "libraries before using papis. You can use "
                           "'papis init /path/to/my/library' for a quick "
                           "interactive setup.")

    # read in configuration from command-line
    sections = configuration.sections()
    for pair in set_list:
        # NOTE: search for a matching section so that we can overwrite entries
        # from the command-line as well (the section takes precedence)
        key, value, section = pair[0], pair[1], None
        for s in sections:
            if key.startswith(s):
                key, section = key[len(s) + 1:], s

        logger.debug("Setting '%s' to '%s' (section '%s').",
                     key, value,
                     section if section else papis.config.GENERAL_SETTINGS_NAME)

        papis.config.set(key, value, section=section)
