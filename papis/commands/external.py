import os
import re
import subprocess
import papis.config
import papis.commands
import click
import logging


logger = logging.getLogger("external")


def get_command_help(path):
    magic_word = papis.config.get("scripts-short-help-regex")
    with open(path) as fd:
        for line in fd:
            m = re.match(magic_word, line)
            if m:
                return m.group(1)
    return "No help message available"


def export_variables():
    """Export environment variables so that external script can access to
    the information
    """
    os.environ["PAPIS_LIB"] = papis.config.get_lib()
    os.environ["PAPIS_LIB_PATH"] = papis.config.get('dir')
    os.environ["PAPIS_CONFIG_PATH"] = papis.config.get_config_folder()
    os.environ["PAPIS_CONFIG_FILE"] = papis.config.get_config_file()
    os.environ["PAPIS_SCRIPTS_PATH"] = papis.config.get_scripts_folder()


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
        help_option_names=[]
    )
)
@click.argument("flags", nargs=-1)
@click.pass_context
def external_cli(ctx, flags):
    script = ctx.obj
    cmd = [script['path']] + list(flags)
    logger.debug("Calling {}".format(cmd))
    export_variables()
    subprocess.call(cmd)
