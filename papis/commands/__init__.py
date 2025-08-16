import copy
import os
import re
from importlib.metadata import EntryPoint
from typing import NamedTuple

import click.core

import papis.config
import papis.logging

#: Name of the entrypoint group for :class:`~click.core.Command` plugins.
COMMAND_EXTENSION_NAME = "papis.command"
#: Regex for determining external commands.
EXTERNAL_COMMAND_REGEX = re.compile(r".*papis-([^ .]+)$")


class FullHelpCommand(click.core.Command):
    """This is a simple wrapper around :class:`click.core.Command` that does
    not truncate the short help messages.

    We still very much prefer that these stay short if at all possible, but the
    default limit of 45 characters does not work well for many non-trivial commands.
    """

    def get_short_help_str(self, limit: int = 45) -> str:
        # NOTE: this is copied from click/core.py::Command.get_short_help_str
        # https://github.com/pallets/click/blob/b7c0ab471c339488766d9413349947b2a7b21543/src/click/core.py#L1067
        # It creates the short help string from the main help string and does not
        # truncate the resulting string to 45 characters like click does.
        import inspect

        if self.short_help:
            text = self.short_help
        elif self.help:
            text = " ".join(self.help.strip().split("\n\n")[0].split())
        else:
            text = ""

        return inspect.cleandoc(text).strip()


class AliasedGroup(click.core.Group):
    """A :class:`click.Group` that accepts command aliases.

    This group command is taken from
    `here <https://click.palletsprojects.com/en/5.x/advanced/#command-aliases>`__
    and is to be used for groups with aliases. In this case, aliases are
    defined as prefixes of the command, so for a command named ``remove``,
    ``rem`` is also accepted as long as it is unique.
    """

    command_class = FullHelpCommand

    def get_command(self,
                    ctx: click.core.Context,
                    cmd_name: str) -> click.core.Command | None:
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
        ctx.fail(f"Too many matches: {matches}")
        return None


class CommandPlugin(NamedTuple):
    """A ``papis`` command plugin or script.

    These plugins are made available through the main ``papis`` command-line
    interface as subcommands.
    """

    #: The name of the command.
    command_name: str
    #: The path to the script if it is a separate executable.
    path: str | None
    #: The module the plugin is imported from if it is an entry point.
    entrypoint: EntryPoint | None


def load_command(cmd: CommandPlugin) -> click.Command | None:
    if cmd.path is not None:
        # we're dealing with an external script: wrap it and hope for the bext
        from papis.commands.external import external_cli, get_command_help

        cli = copy.copy(external_cli)
        cli.name = cmd.command_name
        cli.help = get_command_help(cmd.path)
        cli.short_help = cli.help
        cli.context_settings["obj"] = cmd

        return cli
    elif cmd.entrypoint is not None:
        # we're dealing with an entrypoint plugin: load it
        try:
            plugin = cmd.entrypoint.load()
        except Exception as exc:
            papis.logging.debug("Failed to load plugin '%s' from '%s' (%s).",
                                cmd.command_name, cmd.entrypoint.value, exc)
            return None

        if not isinstance(plugin, click.Command):
            papis.logging.debug("Plugin is not a 'click.Command': '%s',",
                                cmd.entrypoint.value)
            return None

        if not plugin.help:
            plugin.help = "No help message available"

        if not plugin.short_help:
            plugin.short_help = plugin.help

        return plugin
    else:
        papis.logging.debug("Invalid command plugin: '%s'", cmd.command_name)
        return None


def get_external_scripts() -> dict[str, CommandPlugin]:
    """Get a mapping of all external scripts that should be registered with Papis.

    An external script is an executable that can be found in the
    :func:`papis.config.get_scripts_folder` folder or in the user's PATH.
    External scripts are recognized if they are prefixed with ``papis-``.

    :returns: a mapping of scripts that have been found.
    """
    import glob
    paths = [papis.config.get_scripts_folder(), *os.environ.get("PATH", "").split(":")]

    scripts: dict[str, CommandPlugin] = {}
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

            scripts[name] = (
                CommandPlugin(command_name=name, path=script, entrypoint=None))

    return scripts


def get_command_plugins() -> dict[str, CommandPlugin]:
    """Get a mapping of commands that should be registered with Papis.

    This finds all the commands that are registered as entry points in the
    namespace ``"papis.command"``.

    :returns: a mapping of plugins that have been found.
    """
    from papis.plugin import get_entrypoints

    scripts = {}
    for ep in get_entrypoints(COMMAND_EXTENSION_NAME):
        scripts[ep.name] = CommandPlugin(
            command_name=ep.name,
            path=None,
            entrypoint=ep)  # type: ignore[arg-type]

    return scripts


def get_commands() -> dict[str, CommandPlugin]:
    """Get a mapping of all commands that should be registered with Papis.

    This includes the results from :func:`get_external_scripts` and
    :func:`get_command_plugins`. Entrypoint-based scripts take priority, so if an
    external script with the same name is found it is silently ignored.

    :returns: a mapping of scripts that have been found.
    """

    commands = get_command_plugins()
    external_scripts = get_external_scripts()

    for name, script in external_scripts.items():
        cmd = commands.get(name)
        if cmd is not None:
            assert cmd.entrypoint is not None
            papis.logging.debug(
                "WARN: External script '%s' also available as command entry point "
                "from '%s'. Skipping external script!",
                script.path, cmd.entrypoint.value
            )

            continue

        commands[name] = script

    return commands
