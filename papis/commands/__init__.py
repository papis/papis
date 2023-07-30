import os
import re
from typing import Dict, Optional, NamedTuple

import click.core

import papis.config
import papis.logging
import papis.plugin

COMMAND_EXTENSION_NAME = "papis.command"
EXTERNAL_COMMAND_REGEX = re.compile(".*papis-([^ .]+)$")


class AliasedGroup(click.core.Group):
    """A :class:`click.Group` that accepts command aliases.

    This group command is taken from
    `here <https://click.palletsprojects.com/en/5.x/advanced/#command-aliases>`__
    and is to be used for groups with aliases. In this case, aliases are
    defined as prefixes of the command, so for a command named ``remove``,
    ``rem`` is also accepted as long as it is unique.
    """

    def get_command(self,
                    ctx: click.core.Context,
                    cmd_name: str) -> Optional[click.core.Command]:
        """
        :returns: given a context and a command name, this returns a
            :class:`click.Command` object if it exists or returns *None*.
        """
        rv = click.core.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        import difflib
        matches = difflib.get_close_matches(cmd_name, self.list_commands(ctx), n=2)

        if not matches:
            return None
        if len(matches) == 1:
            return click.core.Group.get_command(self, ctx, str(matches[0]))
        ctx.fail("Too many matches: {}".format(matches))
        return None


class Script(NamedTuple):
    """A papis command plugin or script.

    These plugins are made available through the main papis command-line as
    subcommands.
    """

    #: The name of the command.
    command_name: str
    #: The path to the script if it is a separate executable.
    path: Optional[str]
    #: A :class:`click.Command` if the script is registered as an entry point.
    plugin: Optional[click.Command]


def get_external_scripts() -> Dict[str, Script]:
    """Get a mapping of all external scripts that should be registered with papis.

    An external script is an executable that can be found in the
    :func:`papis.config.get_scripts_folder` folder or in the user's PATH.
    External scripts are recognized if they are prefixed with ``papis-``.

    :returns: a mapping of scripts that have been found.
    """
    import glob
    paths = [papis.config.get_scripts_folder()] + os.environ.get("PATH", "").split(":")

    scripts: Dict[str, Script] = {}
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
    """Get a mapping of commands that should be registered with papis.

    This finds all the commands that are registered as entry points in the
    namespace ``"papis.command"``.

    :returns: a mapping of scripts that have been found.
    """
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
    """Get a mapping of all commands that should be registered with papis.

    This includes the results from :func:`get_external_scripts` and
    :func:`get_scripts`. Entrypoint-based scripts take priority, so if an
    external script with the same name is found it is silently ignored.

    :returns: a mapping of scripts that have been found.
    """

    scripts = get_scripts()
    external_scripts = get_external_scripts()

    for name, script in external_scripts.items():
        entry_point_script = scripts.get(name)
        if entry_point_script is not None:
            plugin = entry_point_script.plugin
            assert plugin is not None

            papis.logging.debug(
                "WARN: External script '%s' also available as command entry point "
                "from '%s'. Skipping external script!",
                script.path, plugin.callback.__module__
                )

            continue

        scripts[name] = script

    return scripts
