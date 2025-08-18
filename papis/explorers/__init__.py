from functools import cached_property
from typing import Any

import click

import papis.cli
from papis.commands import CommandPlugin, CommandPluginLoaderGroup, get_commands

#: Name of the entry point namespace for explorer plugins.
EXPLORER_NAMESPACE_NAME = "papis.explorer"


class ExplorerLoaderGroup(CommandPluginLoaderGroup):
    @cached_property
    def command_plugins(self) -> dict[str, CommandPlugin]:
        return get_commands(EXPLORER_NAMESPACE_NAME, extern_matcher=False)


def as_explorer(name: str) -> papis.cli.DecoratorCallable:
    """Adds standard options to an explorer command."""
    def wrapper(f: papis.cli.DecoratorCallable) -> Any:
        f = click.help_option("-h", "--help")(f)
        f = click.pass_context(f)
        f = click.command(name)(f)

        return f

    return wrapper


def get_available_explorers() -> list[str]:
    """Gets all registered explorers."""
    from papis.plugin import get_plugin_names

    return get_plugin_names(EXPLORER_NAMESPACE_NAME)


def get_explorer_by_name(name: str) -> click.Command:
    """Get the explorer with name *name*.

    Explorer plugins are automatically loaded by the ``papis explore`` command.
    This function is just provided for testing.
    """
    from papis.plugin import (
        InvalidPluginTypeError,
        PluginNotFoundError,
        get_plugin_by_name,
    )

    cls = get_plugin_by_name(EXPLORER_NAMESPACE_NAME, name)
    if cls is None:
        raise PluginNotFoundError(EXPLORER_NAMESPACE_NAME, name)

    if not isinstance(cls, click.Command):
        raise InvalidPluginTypeError(EXPLORER_NAMESPACE_NAME, name)

    return cls
