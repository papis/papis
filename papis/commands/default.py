"""
Examples
^^^^^^^^

- To override some configuration options, you can use the flag ``--set``, for
  instance, if you want to override the editor used and the opentool to open
  documents, you can just type

    .. code:: shell

        papis --set editor gedit --set opentool firefox edit
        papis --set editor gedit --set opentool firefox open

- If you want to list the libraries and pick one before sending a database
  query to papis, use ``--pick-lib`` as such

    .. code:: shell

        papis --pick-lib open 'einstein relativity'

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.default:run
    :prog: papis
"""

import os
from typing import Optional, Tuple, List, Callable, TYPE_CHECKING

import click
import click.core

import papis
import papis.api
import papis.cli
import papis.config
import papis.logging
import papis.commands
import papis.database

if TYPE_CHECKING:
    import cProfile

logger = papis.logging.get_logger(__name__)


class MultiCommand(click.core.MultiCommand):

    scripts = papis.commands.get_scripts()
    scripts.update(papis.commands.get_external_scripts())

    def list_commands(self, ctx: click.core.Context) -> List[str]:
        """List all matched commands in the command folder and in path

        >>> mc = MultiCommand()
        >>> rv = mc.list_commands(None)
        >>> len(rv) > 0
        True
        """
        _rv = list(self.scripts)
        _rv.sort()
        return _rv

    def get_command(
            self,
            ctx: click.core.Context,
            name: str) -> Optional[click.core.Command]:
        """Get the command to be run

        >>> mc = MultiCommand()
        >>> cmd = mc.get_command(None, 'add')
        >>> cmd.name, cmd.help
        ('add', 'Add...')
        >>> mc.get_command(None, 'this command does not exist')
        Command ... is unknown!
        """
        try:
            script = self.scripts[name]
        except KeyError:
            import difflib
            matches = list(map(
                str, difflib.get_close_matches(name, self.scripts, n=2)))

            if matches:
                click.echo("Command '{name}' is unknown! Did you mean '{matches}'?"
                           .format(name=name, matches="' or '".join(matches)))
            else:
                click.echo("Command '{name}' is unknown!".format(name=name))

            # return the match if there was only one match
            if len(matches) == 1:
                click.echo("I suppose you meant: '{}'".format(matches[0]))
                script = self.scripts[matches[0]]
            else:
                return None

        if script.plugin is not None:
            return script.plugin

        # If it gets here, it means that it is an external script
        import copy
        from papis.commands.external import external_cli
        cli = copy.copy(external_cli)

        from papis.commands.external import get_command_help
        cli.context_settings["obj"] = script
        if script.path is not None:
            cli.help = get_command_help(script.path)
        cli.name = script.command_name
        cli.short_help = cli.help
        return cli


def generate_profile_writing_function(profiler: "cProfile.Profile",
                                      filename: str) -> Callable[[], None]:
    def _on_finish() -> None:
        profiler.disable()
        profiler.dump_stats(filename)

    return _on_finish


@click.group(
    cls=MultiCommand,
    invoke_without_command=True)
@click.help_option("--help", "-h")
@click.version_option(version=papis.__version__)
@click.option(
    "-v",
    "--verbose",
    help="Make the output verbose (equivalent to --log DEBUG)",
    default="PAPIS_DEBUG" in os.environ,
    is_flag=True)
@click.option(
    "--profile",
    help="Print profiling information into file",
    type=click.Path(),
    default=None)
@click.option(
    "-l",
    "--lib",
    help="Choose a library name or library path (unnamed library)",
    default=lambda: papis.config.getstring("default-library"))
@click.option(
    "-c",
    "--config",
    help="Configuration file to use",
    type=click.Path(exists=True),
    default=None)
@click.option(
    "--pick-lib",
    help="Pick library to use",
    default=False,
    is_flag=True)
@click.option(
    "--cc", "--clear-cache", "clear_cache",
    help="Clear cache of the library used",
    default=False,
    is_flag=True)
@click.option(
    "-s", "--set", "set_list",
    type=(str, str),
    multiple=True,
    help="Set key value, e.g., "
         "--set info-name information.yaml --set opentool evince")
@click.option(
    "--color",
    type=click.Choice(["always", "auto", "no"]),
    default=os.environ.get("PAPIS_LOG_COLOR", "auto"),
    help="Prevent the output from having color")
@click.option(
    "--log",
    help="Logging level",
    type=click.Choice(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]),
    default=os.environ.get("PAPIS_LOG_LEVEL", "INFO"))
@click.option(
    "--logfile",
    help="File to dump the log",
    type=str,
    default=os.environ.get("PAPIS_LOG_FILE"))
@click.option(
    "--np",
    help="Use number of processors for multicore functionalities in papis",
    type=str,
    default=None)
def run(verbose: bool,
        profile: str,
        config: str,
        lib: str,
        log: str,
        logfile: Optional[str],
        pick_lib: bool,
        clear_cache: bool,
        set_list: List[Tuple[str, str]],
        color: str,
        np: Optional[int]) -> None:

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
        picked_libs = papis.pick.pick(papis.api.get_libraries())
        if picked_libs:
            lib = picked_libs[0]

    papis.config.set_lib_from_name(lib)
    library = papis.config.get_lib()

    if not library.paths:
        raise RuntimeError(
            "Library '{}' does not have any existing folders attached to it. "
            "Please define and create the paths in the configuration file"
            .format(lib))

    # Now the library should be set, let us check if there is a
    # local configuration file there, and if there is one, then
    # merge its contents
    local_config_file = papis.config.getstring("local-config-file")
    for path in library.paths:
        local_config_path = os.path.expanduser(os.path.join(path, local_config_file))
        papis.config.merge_configuration_from_path(
            local_config_path,
            papis.config.get_configuration())

    # read in configuration from command-line
    for pair in set_list:
        logger.debug("Setting '%s' to '%s'.", *pair)
        papis.config.set(pair[0], pair[1])

    if clear_cache:
        papis.database.get().clear()
