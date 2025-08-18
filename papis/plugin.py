from importlib.metadata import EntryPoint, entry_points
from typing import Any

import papis.logging

logger = papis.logging.get_logger(__name__)


class PluginError(Exception):
    """A generic error raised by the plugin loader."""


class PluginNotFoundError(PluginError):
    """An error raised when a plugin is not found."""

    def __init__(self, namespace: str, name: str) -> None:
        names = "', '".join(get_plugin_names(namespace))
        super().__init__(f"plugin '{name}' from namespace '{namespace}' was not "
                         f"found (known plugins are '{names}')")


class InvalidPluginTypeError(PluginError):
    """An error raised when the plugin is not the expected type."""

    def __init__(self, namespace: str, name: str) -> None:
        super().__init__(f"plugin '{name}' from namespace '{namespace}' has an "
                         f"unexpected type")


def get_entrypoints(namespace: str) -> list[EntryPoint]:
    """
    :returns: a list of available entrypoints in the given *namespace*.
    """
    return sorted(entry_points(group=namespace))


def get_entrypoint_by_name(namespace: str, name: str) -> EntryPoint | None:
    """Get the entrypoint *name* from the given *namespace*.

    If no such entrypoint exists, then *None* is returned. To load the plugin
    defined by the entrypoint, use ``Entrypoint.load``.
    """
    entrypoints = entry_points(group=namespace).select(name=name)
    if len(entrypoints) == 1:
        return entrypoints[name]  # type: ignore[no-any-return]

    return None


def get_plugin_names(namespace: str) -> list[str]:
    """
    :returns: a list of available entrypoint names in the given *namespace*.
    """
    return sorted(entry_points(group=namespace).names)


def get_plugins(namespace: str) -> dict[str, Any]:
    """Load all available plugins from *namespace*."""

    result = {}
    for ep in get_entrypoints(namespace):
        try:
            plugin = ep.load()
        except Exception as exc:
            logger.error("Failed to load plugin '%s' from namespace '%s'.",
                         ep.name, namespace, exc_info=exc)
            continue

        result[ep.name] = plugin

    return result


def get_plugin_by_name(namespace: str, name: str) -> Any:
    """Load a single plugin named *name* from *namespace*."""
    ep = get_entrypoint_by_name(namespace, name)
    if ep is None:
        raise PluginNotFoundError(namespace, name)

    try:
        return ep.load()
    except Exception as exc:
        logger.error("Failed to load plugin '%s' from namespace '%s'.",
                     ep.name, namespace, exc_info=exc)
        return None
