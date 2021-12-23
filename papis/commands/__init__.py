import os
import re
import glob
from typing import Dict, Optional, Union, NamedTuple

from click.core import Command

import papis.cli
import papis.config
import papis.plugin


Script = NamedTuple("Script",
                    [("command_name", str),
                     ("path", Optional[str]),
                     ("plugin", Union[None, Command, papis.cli.AliasedGroup])])


def get_external_scripts() -> Dict[str, Script]:
    regex = re.compile('.*papis-([^ .]+)$')
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
    scripts_dict = dict()
    for command_name in commands_mgr.names():
        scripts_dict[command_name] = Script(
            command_name=command_name,
            path=None,
            plugin=commands_mgr[command_name].plugin
        )
    return scripts_dict
