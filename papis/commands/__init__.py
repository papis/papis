import os
import re
import glob
from typing import Dict, Optional, Union, NamedTuple
import difflib

import click.core

import papis.config
import papis.logging
import papis.plugin

COMMAND_EXTENSION_NAME = "papis.command"
EXTERNAL_COMMAND_REGEX = re.compile(".*papis-([^ .]+)$")


class AliasedGroup(click.core.Group):
    """
    This group command is taken from
    `here <https://click.palletsprojects.com/en/5.x/advanced/#command-aliases>`__
    and is to be used for groups with aliases.
    """

    def get_command(self,
                    ctx: click.core.Context,
                    cmd_name: str) -> Optional[click.core.Command]:
        rv = click.core.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        matches = difflib.get_close_matches(
            cmd_name, self.list_commands(ctx), n=2)
        if not matches:
            return None
        if len(matches) == 1:
            return click.core.Group.get_command(self, ctx, str(matches[0]))
        ctx.fail("Too many matches: {}".format(matches))
        return None


class Script(NamedTuple):
    command_name: str
    path: Optional[str]
    plugin: Optional[Union[click.Command, AliasedGroup]]


def get_external_scripts() -> Dict[str, Script]:
    paths = [papis.config.get_scripts_folder()] + os.environ.get("PATH", "").split(":")

    scripts = {}
    for path in paths:
        for script in glob.iglob(os.path.join(path, "papis-*")):
            m = EXTERNAL_COMMAND_REGEX.match(script)
            if m is None:
                continue

            name = m.group(1)
            if name in scripts:
                papis.logging.debug(
                    "WARN: External script '%s' with name '%s' already "
                    "found at '%s'. Overwriting the previous script!",
                    script, name, scripts[name].path)

            scripts[name] = Script(command_name=name, path=script, plugin=None)

    return scripts


def get_scripts() -> Dict[str, Script]:
    mgr = papis.plugin.get_extension_manager(COMMAND_EXTENSION_NAME)

    scripts = {}
    for name in mgr.names():
        extension = mgr[name]

        plugin = extension.plugin
        if not plugin.help:
            plugin.help = "No help message available"

        if not plugin.short_help:
            plugin.short_help = plugin.help

        scripts[name] = Script(command_name=name, path=None, plugin=plugin)

    return scripts


def get_all_scripts() -> Dict[str, Script]:
    scripts = get_scripts()
    external_scripts = get_external_scripts()

    for name, script in external_scripts.items():
        entry_point_script = scripts.get(name)
        if entry_point_script is not None:
            papis.logging.debug(
                "WARN: External script '%s' also available as command entry point "
                "from '%s'. Skipping external script!",
                script.path, entry_point_script.plugin.callback.__module__
                )

            continue

        scripts[name] = script

    return scripts
