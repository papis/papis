from collections.abc import Callable
from typing import TypeAlias, cast

from papis.document import Document

#: Name of the entry point namespace for exporter plugins.
EXPORTER_NAMESPACE_NAME = "papis.exporter"
#: Type alias for an exporter callable.
Exporter: TypeAlias = Callable[[list[Document]], str]


def get_available_exporters() -> list[str]:
    """Gets all registered exporters."""
    from papis.plugin import get_plugin_names

    return get_plugin_names(EXPORTER_NAMESPACE_NAME)


def get_exporter_by_name(name: str) -> Exporter:
    """Get the exporter with name *name*."""
    from papis.plugin import (
        InvalidPluginTypeError,
        PluginNotFoundError,
        get_plugin_by_name,
    )

    func = get_plugin_by_name(EXPORTER_NAMESPACE_NAME, name)
    if func is None:
        raise PluginNotFoundError(EXPORTER_NAMESPACE_NAME, name)

    # TODO: do we want to do stricter checking here? using the `inspect` module
    # will do the trick, but it's a pretty heavy import
    if not callable(func):
        raise InvalidPluginTypeError(EXPORTER_NAMESPACE_NAME, name)

    return cast("Exporter", func)
