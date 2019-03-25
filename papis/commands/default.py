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
import sys
import papis
import papis.api
import papis.config
import papis.commands
import papis.database
import colorama
import logging
import click
import papis.cli


@click.group(
    cls=papis.cli.MultiCommand,
    invoke_without_command=False
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
    type=click.Choice(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO"
)
@click.option(
    "--pick-lib",
    help="Pick library to use",
    default=False,
    is_flag=True
)
@click.option(
    "--cc", "--clear-cache", "clear_cache",
    help="Clear cache of the library used",
    default=False,
    is_flag=True
)
@click.option(
    "-s", "--set", "set_list",
    type=(str, str),
    multiple=True,
    help="Set key value, e.g., "
         "--set info-name information.yaml  --set opentool evince",
)
@click.option(
    "--color",
    type=click.Choice(["always", "auto", "no"]),
    default="auto",
    help="Prevent the output from having color"
)
def run(
        verbose,
        config,
        lib,
        log,
        pick_lib,
        clear_cache,
        set_list,
        color
        ):

    if color == "no" or (color == "auto" and not sys.stdout.isatty()):
        # Turn off colorama (strip escape sequences from the output)
        colorama.init(strip=True)
    else:
        colorama.init()

    log_format = (
        colorama.Fore.YELLOW +
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
    logging.basicConfig(
        level=getattr(logging, log),
        format=log_format
    )
    logger = logging.getLogger('default')

    for pair in set_list:
        logger.debug('Setting "{0}" to "{1}"'.format(*pair))
        papis.config.set(pair[0], pair[1])

    if config:
        papis.config.set_config_file(config)
        papis.config.reset_configuration()

    if pick_lib:
        lib = papis.pick.pick(
            papis.api.get_libraries(),
            pick_config=dict(header_filter=lambda x: x)
        )

    papis.config.set_lib_from_name(lib)
    library = papis.config.get_lib()

    for path in library.paths:
        # Now the library should be set, let us check if there is a
        # local configuration file there, and if there is one, then
        # merge its contents
        local_config_file = os.path.expanduser(
            os.path.join(
                path,
                papis.config.get("local-config-file")
            )
        )
        papis.config.merge_configuration_from_path(
            local_config_file,
            papis.config.get_configuration()
        )

    if clear_cache:
        papis.database.get().clear()
