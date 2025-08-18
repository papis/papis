import copy
import os
import re
from functools import cached_property
from importlib.metadata import EntryPoint
from typing import Any, Literal, NamedTuple

import click

#: Name of the entry point namespace for :class:`~click.Command` plugins.
COMMAND_NAMESPACE_NAME = "papis.command"
#: Regex for determining external commands.
EXTERNAL_COMMAND_REGEX = re.compile(r".*papis-([^ .]+)$")


def debug(msg: str, *args: Any) -> None:
    if "PAPIS_DEBUG" in os.environ:
        click.echo(msg % args)


class FullHelpCommand(click.Command):
    """This is a simple wrapper around :class:`click.Command` that does
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


class AliasedGroup(click.Group):
    """A :class:`click.Group` that accepts command aliases.

    This group command is taken from
    `here <https://click.palletsprojects.com/en/5.x/advanced/#command-aliases>`__
    and is to be used for groups with aliases. In this case, aliases are
    defined as prefixes of the command. For example, for a command named ``remove``,
    ``rem`` is also accepted as long as it is unique.
    """

    command_class = FullHelpCommand

    def get_command(self,
                    ctx: click.Context,
                    cmd_name: str) -> click.Command | None:
        """
        :returns: given a context and a command name, this returns a
            :class:`click.Command` object if it exists or returns *None*.
        """
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv

        import difflib
        matches = difflib.get_close_matches(cmd_name, self.list_commands(ctx), n=2)

        if not matches:
            return None
        if len(matches) == 1:
            return super().get_command(ctx, str(matches[0]))

        ctx.fail(f"Too many matches: {matches}")
        return None


class CommandPluginLoaderGroup(click.Group):
    """A :class:`click.Group` that loads additional commands from entry points.

    Commands in this group are loaded using :func:`get_commands`. By default
    commands from the :data:`COMMAND_NAMESPACE_NAME` namespace are loaded.
    Additional external scripts that are found in the path and match the
    :data:`EXTERNAL_COMMAND_REGEX` are also loaded.

    To overwrite this behavior, create a subclass and modify the
    :meth:`command_plugins` method to load commands from other namespaces.
    """

    command_class = FullHelpCommand

    @cached_property
    def command_plugins(self) -> dict[str, "CommandPlugin"]:
        """A mapping of command names to available command plugins."""
        return get_commands(COMMAND_NAMESPACE_NAME,
                            extern_matcher=EXTERNAL_COMMAND_REGEX)

    @cached_property
    def command_plugin_names(self) -> list[str]:
        """A list of all commands available through plugins."""
        return sorted(self.command_plugins)

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List all matched commands in the command folder and in path

        >>> group = CommandPluginLoaderGroup()
        >>> rv = group.list_commands(None)
        >>> len(rv) > 0
        True
        """
        # FIXME: this should check and yell if any existing commands are overwritten
        return sorted({*super().list_commands(ctx), *self.command_plugin_names})

    def get_command(
            self,
            ctx: click.Context,
            name: str) -> click.Command | None:
        """Get the command to be run

        >>> group = CommandPluginLoaderGroup()
        >>> cmd = group.get_command(None, 'add')
        >>> cmd.name, cmd.help
        ('add', 'Add...')
        >>> group.get_command(None, 'this command does not exist')
        Command ... is unknown!
        """

        # NOTE: allow using the standard `@group.command(name)` functionality
        cmd = super().get_command(ctx, name)
        if cmd is not None:
            return cmd

        try:
            plugin = self.command_plugins[name]
        except KeyError:
            import difflib

            # FIXME: this should probably also look for commands that click
            # already knows about (from `@group.command(name)`)
            matches = list(map(
                str, difflib.get_close_matches(name, self.command_plugin_names, n=2)))

            click.echo(f"Command '{name}' is unknown!")
            if len(matches) == 1:
                # return the match if there was only one match
                click.echo(f"I suppose you meant: '{matches[0]}'")
                plugin = self.command_plugins[matches[0]]
            elif matches:
                click.echo("Did you mean '{matches}'?"
                           .format(matches="' or '".join(matches)))
                return None
            else:
                return None

        return load_command(plugin)


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
    """Load a command based on the given information in *cmd*.

    * If the command is an entry point, then it is loaded through the mechanisms
      in :mod:`importlib.metadata`.
    * If the command is an external executable, it is wrapped as an external
      command and all command-line arguments are passed through to it.

    :returns: a :class:`click.Command` that can be used by a :class:`click.Group`.
    """

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
            debug("Failed to load plugin '%s' from '%s' (%s).",
                  cmd.command_name, cmd.entrypoint.value, exc)
            return None

        if not isinstance(plugin, click.Command):
            debug("Plugin is not a 'click.Command': '%s',",
                  cmd.entrypoint.value)
            return None

        if plugin.help:
            if not plugin.short_help:
                plugin.short_help = (
                    " ".join(plugin.help.strip().split("\n\n")[0].split()))
        else:
            if plugin.short_help:
                plugin.help = plugin.short_help
            else:
                plugin.help = plugin.short_help = "No help message available"

        return plugin
    else:
        debug("Invalid command plugin: '%s'", cmd.command_name)
        return None


def get_external_scripts(
        matcher: re.Pattern[str] | None = None) -> dict[str, CommandPlugin]:
    """Get a mapping of all external scripts that should be registered with Papis.

    An external script is an executable that can be found in the
    :func:`papis.config.get_scripts_folder` folder or in the user's PATH.
    The scripts are recognized by their file name using the provided *matcher*
    regular expression. For example, default Papis commands are always recognized
    using :data:`EXTERNAL_COMMAND_REGEX`.

    :returns: a mapping of scripts that have been found.
    """
    import glob

    if matcher is None:
        matcher = EXTERNAL_COMMAND_REGEX

    from papis.config import get_scripts_folder

    paths = [get_scripts_folder(), *os.environ.get("PATH", "").split(":")]

    scripts: dict[str, CommandPlugin] = {}
    for path in paths:
        for script in glob.iglob(os.path.join(path, "papis-*")):
            m = matcher.match(script)
            if m is None:
                continue

            name = m.group(1)
            if name in scripts:
                debug(
                    "WARN: External script '%s' with name '%s' already "
                    "found at '%s'. Overwriting the previous script!",
                    script, name, scripts[name].path)

            scripts[name] = (
                CommandPlugin(command_name=name, path=script, entrypoint=None))

    return scripts


def get_command_plugins(namespace: str) -> dict[str, CommandPlugin]:
    """Get a mapping of entry points that should be registered as Papis commands.

    :param namespace: a namespace for the entry point commands to retrieve.
    :returns: a mapping of plugins that have been found.
    """
    from papis.plugin import get_entrypoints

    scripts = {}
    for ep in get_entrypoints(namespace):
        scripts[ep.name] = CommandPlugin(
            command_name=ep.name,
            path=None,
            entrypoint=ep)  # type: ignore[arg-type]

    return scripts


def get_commands(
        namespace: str, *,
        extern_matcher: re.Pattern[str] | Literal[False] | None = None,
    ) -> dict[str, CommandPlugin]:
    """Get a mapping of all commands that should be registered with Papis.

    This includes the results from :func:`get_external_scripts` and
    :func:`get_command_plugins`. Entrypoint-based scripts take priority, so if an
    external script with the same name is found it is silently ignored.

    :param namespace: a namespace for the entry point commands to retrieve.
    :param extern_matcher: a regular expression that matches file names of
        external commands (see :func:`get_external_scripts`). If *False*, no
        external commands are loaded.
    :returns: a mapping of scripts that have been found.
    """
    if extern_matcher is None:
        extern_matcher = EXTERNAL_COMMAND_REGEX

    commands = get_command_plugins(namespace)

    if extern_matcher is not False:
        external_scripts = get_external_scripts(extern_matcher)

        for name, script in external_scripts.items():
            cmd = commands.get(name)
            if cmd is not None:
                assert cmd.entrypoint is not None
                debug(
                    "WARN: External script '%s' also available as command entry point "
                    "from '%s'. Skipping external script!",
                    script.path, cmd.entrypoint.value
                )

                continue

            commands[name] = script

    return commands
