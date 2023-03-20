import os
import re
import glob
from typing import Dict, Optional, Union, NamedTuple
import difflib

import click.core

import papis.config
import papis.plugin


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


Script = NamedTuple("Script",
                    [("command_name", str),
                     ("path", Optional[str]),
                     ("plugin", Union[None,
                                      click.core.Command,
                                      AliasedGroup])])


def get_external_scripts() -> Dict[str, Script]:
    regex = re.compile(".*papis-([^ .]+)$")
    paths = []
    scripts = {}
    paths.append(papis.config.get_scripts_folder())
    paths += os.environ["PATH"].split(":")
    for path in paths:
        for script in glob.glob(os.path.join(path, "papis-*")):
            m = regex.match(script)
            if m is not None:
                name = m.group(1)
                scripts[name] = Script(command_name=name,
                                       path=script,
                                       plugin=None)
    return scripts


def _extension_name() -> str:
    return "papis.command"


def get_scripts() -> Dict[str, Script]:
    commands_mgr = papis.plugin.get_extension_manager(_extension_name())

    scripts_dict = {}
    for command_name in commands_mgr.names():
        scripts_dict[command_name] = Script(
            command_name=command_name,
            path=None,
            plugin=commands_mgr[command_name].plugin
        )

    return scripts_dict
