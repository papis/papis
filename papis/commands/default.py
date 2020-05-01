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

Cli
^^^
.. click:: papis.commands.default:run
    :prog: papis
    :commands: []

"""
import os
import difflib
import sys
import logging
from typing import Optional, Tuple, List, Callable

import papis
import papis.api
import papis.config
import papis.commands
import papis.database
import papis.cli

import atexit
import cProfile
import pstats
import colorama
import click
import click.core


class MultiCommand(click.core.MultiCommand):

    scripts = papis.commands.get_scripts()
    scripts.update(papis.commands.get_external_scripts())
    logger = logging.getLogger('multicommand')

    def list_commands(self, ctx: click.core.Context) -> List[str]:
        """List all matched commands in the command folder and in path

        >>> mc = MultiCommand()
        >>> rv = mc.list_commands(None)
        >>> len(rv) > 0
        True
        """
        _rv = list(self.scripts.keys())
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
        """
        try:
            script = self.scripts[name]
        except KeyError:
            matches = list(map(
                str, difflib.get_close_matches(name, self.scripts, n=2)))
            self.logger.error(
                '{c.Fore.RED}{c.Style.BRIGHT}{c.Back.BLACK}'
                'did you mean {0}?'
                '{c.Style.RESET_ALL}'
                .format(
                    ' or '.join(matches),
                    c=colorama
                ))
            # return the match if there was only one match
            if len(matches) == 1:
                self.logger.warning("I suppose you meant: '%s'", *matches)
                script = self.scripts[matches[0]]
            else:
                return None

        if script.plugin is not None:
            return script.plugin
        # If it gets here, it means that it is an external script
        from papis.commands.external import external_cli as cli
        from papis.commands.external import get_command_help
        cli.context_settings['obj'] = script
        if script.path is not None:
            cli.help = get_command_help(script.path)
        cli.name = script.command_name
        cli.short_help = cli.help
        return cli


def generate_profile_writing_function(profiler: cProfile.Profile,
                                      filename: str) -> Callable[[], None]:
    def _on_finish() -> None:
        profiler.disable()
        profiler.create_stats()
        with open(filename, 'w') as output:
            stats = pstats.Stats(profiler, stream=output)
            stats.sort_stats('time')
            stats.print_stats()

    return _on_finish


@click.group(
    cls=MultiCommand,
    invoke_without_command=True)
@click.help_option('--help', '-h')
@click.version_option(version=papis.__version__)
@click.option(
    "-v",
    "--verbose",
    help="Make the output verbose (equivalent to --log DEBUG)",
    default=False,
    is_flag=True)
@click.option(
    "--profile",
    help="Print profiling information into file",
    type=click.Path(),
    default=None)
@click.option(
    "-l",
    "--lib",
    help="Choose a library name or library path (unamed library)",
    default=lambda: papis.config.getstring("default-library"))
@click.option(
    "-c",
    "--config",
    help="Configuration file to use",
    type=click.Path(exists=True),
    default=None,)
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
         "--set info-name information.yaml  --set opentool evince",)
@click.option(
    "--color",
    type=click.Choice(["always", "auto", "no"]),
    default="auto",
    help="Prevent the output from having color")
@click.option(
    "--log",
    help="Logging level",
    type=click.Choice(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO")
@click.option(
    "--logfile",
    help="File to dump the log",
    type=str,
    default=None)
def run(
        verbose: bool,
        profile: str,
        config: str,
        lib: str,
        log: str,
        logfile: Optional[str],
        pick_lib: bool,
        clear_cache: bool,
        set_list: List[Tuple[str, str]],
        color: str) -> None:

    if profile:
        profiler = cProfile.Profile()
        profiler.enable()
        atexit.register(generate_profile_writing_function(profiler, profile))

    if color == "no" or (color == "auto" and not sys.stdout.isatty()):
        # Turn off colorama (strip escape sequences from the output)
        colorama.init(strip=True)
    else:
        colorama.init()

    log_format = (colorama.Fore.YELLOW +
                  '%(levelname)s' +
                  ':' +
                  colorama.Fore.GREEN +
                  '%(name)s' +
                  colorama.Style.RESET_ALL +
                  ':' +
                  '%(message)s'
                  )
    if verbose:
        log = "DEBUG"
        log_format = '%(relativeCreated)d-'+log_format
    logging.basicConfig(level=getattr(logging, log),
                        format=log_format,
                        filename=logfile,
                        filemode='w+' if logfile is not None else 'a')
    logger = logging.getLogger('default')

    if config:
        papis.config.set_config_file(config)
        papis.config.reset_configuration()

    for pair in set_list:
        logger.debug('Setting "{0}" to "{1}"'.format(*pair))
        papis.config.set(pair[0], pair[1])

    if pick_lib:
        _picked_libs = papis.pick.pick(papis.api.get_libraries())
        if _picked_libs:
            lib = _picked_libs[0]

    papis.config.set_lib_from_name(lib)
    library = papis.config.get_lib()

    if not library.paths:
        raise Exception("Library '{0}' does not have any existing folders"
                        " attached to it, please define and create the paths"
                        .format(lib))

    for path in library.paths:
        # Now the library should be set, let us check if there is a
        # local configuration file there, and if there is one, then
        # merge its contents
        local_config_file = os.path.expanduser(
            os.path.join(path,
                         papis.config.getstring("local-config-file")))
        papis.config.merge_configuration_from_path(
            local_config_file,
            papis.config.get_configuration())

    if clear_cache:
        papis.database.get().clear()
