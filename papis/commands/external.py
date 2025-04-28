"""
This module define the entry point for external scripts to be called by papis.
"""

import os
import re
from typing import Any, Dict, List, Optional

import click

import papis.utils
import papis.config
import papis.commands
import papis.logging

logger = papis.logging.get_logger(__name__)


def get_command_help(path: str) -> str:
    """Get help string from external commands."""
    magic_word = papis.config.getstring("scripts-short-help-regex")
    with open(path, encoding="utf-8") as fd:
        for line in fd:
            match = re.match(magic_word, line)
            if match:
                return str(match.group(1))

    return "No help message available"


def get_exported_variables(ctx: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Export environment variables so that external script can access to
    the information
    """
    exports = {
        "PAPIS_LIB": papis.config.get_lib().name,
        "PAPIS_LIB_PATH": papis.config.get_lib().path_format(),
        "PAPIS_CONFIG_PATH": papis.config.get_config_folder(),
        "PAPIS_CONFIG_FILE": papis.config.get_config_file(),
        "PAPIS_SCRIPTS_PATH": papis.config.get_scripts_folder(),
    }

    if ctx is not None:
        if ctx.get("verbose"):
            exports["PAPIS_DEBUG"] = "1"
        if ctx.get("log"):
            exports["PAPIS_LOG_LEVEL"] = str(ctx["log"])
        if ctx.get("color"):
            exports["PAPIS_LOG_COLOR"] = str(ctx["color"])
        if ctx.get("logfile"):
            exports["PAPIS_LOG_FILE"] = str(ctx["logfile"])

    return exports


@click.command(
    context_settings={
        "ignore_unknown_options": True,
        "help_option_names": [],
        }
    )
@click.argument("flags", nargs=-1)
@click.pass_context
def external_cli(ctx: click.core.Context, flags: List[str]) -> None:
    """Actual papis command to call the external command"""
    script: papis.commands.Script = ctx.obj
    path = script.path
    if not path:
        raise FileNotFoundError(f"Path for script '{script}' not found")

    cmd = [path, *flags]
    logger.debug("Calling external command '%s'.", cmd)

    params = ctx.parent.params if ctx.parent else {}
    environ = os.environ.copy()
    environ.update(get_exported_variables(params))

    papis.utils.run(cmd, env=environ)
