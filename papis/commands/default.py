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
import papis
import papis.api
import papis.config
import papis.commands
import logging
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
    "-s", "--set",
    type=(str, str),
    multiple=True,
    help="Set key value, e.g., "
         "--set info-name information.yaml  --set opentool evince",
)
def run(
        verbose,
        config,
        lib,
        log,
        pick_lib,
        cc,
        cores,
        set
        ):
    log_format = '%(levelname)s:%(name)s:%(message)s'
    if verbose:
        log = "DEBUG"
        log_format = '%(relativeCreated)d-'+log_format
    logging.basicConfig(
        level=getattr(logging, log),
        format=log_format
    )

    for pair in set:
        papis.config.set(pair[0], pair[1])

    if config:
        papis.config.set_config_file(config)
        papis.config.reset_configuration()

    if pick_lib:
        lib = papis.api.pick(
            papis.api.get_libraries(),
            pick_config=dict(header_filter=lambda x: x)
        )

    papis.config.set_lib(lib)

    # Now the library should be set, let us check if there is a
    # local configuration file there, and if there is one, then
    # merge its contents
    local_config_file = os.path.expanduser(
        os.path.join(
            papis.config.get("dir"),
            papis.config.get("local-config-file")
        )
    )
    papis.config.merge_configuration_from_path(
        local_config_file,
        papis.config.get_configuration()
    )

    if cc:
        papis.api.clear_lib_cache(lib)
