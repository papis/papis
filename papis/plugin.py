import sys

if sys.version_info[:2] >= (3, 10):
    from importlib.metadata import EntryPoint, entry_points
else:
    # NOTE: `entry_points` got a keyword argument in 3.10 that we need
    from importlib_metadata import EntryPoint, entry_points

from typing import Any, Dict, List, Optional

import papis.logging

logger = papis.logging.get_logger(__name__)


def get_entrypoints(namespace: str) -> List[EntryPoint]:
    """
    :returns: a list of available entrypoints in the given *namespace*.
    """
    return sorted(entry_points(group=namespace))


def get_entrypoint_by_name(namespace: str, name: str) -> Optional[EntryPoint]:
    """Get the entrypoint *name* from the given *namespace*.

    If no such entrypoint exists, then *None* is returned. To load the plugin
    defined by the entrypoint, use :meth:`importlib.metadata.Entrypoint.load`.
    """
    entrypoints = entry_points(group=namespace).select(name=name)
    if len(entrypoints) == 1:
        return entrypoints[name]  # type: ignore[no-any-return]

    return None


def get_plugin_names(namespace: str) -> List[str]:
    """
    :returns: a list of available entrypoint names in the given *namespace*.
    """
    return sorted(entry_points(group=namespace).names)


def get_plugins(namespace: str) -> Dict[str, Any]:
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


def get_plugin_by_name(namespace: str, name: str) -> Optional[Any]:
    """Load a single plugin named *name* from *namespace*."""
    ep = get_entrypoint_by_name(namespace, name)
    if ep is None:
        return None

    try:
        return ep.load()
    except Exception as exc:
        logger.error("Failed to load plugin '%s' from namespace '%s'.",
                     ep.name, namespace, exc_info=exc)
        return None
