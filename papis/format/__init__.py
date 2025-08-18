from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar

import papis.logging

if TYPE_CHECKING:
    from papis.document import DocumentLike
    from papis.strings import AnyString

logger = papis.logging.get_logger(__name__)

# A cache for loaded formatters
FORMATTER_CACHE: dict[str, "Formatter"] = {}
#: Name of the entry point namespace for :class:`Formatter` plugins.
FORMATTER_NAMESPACE_NAME = "papis.format"


class InvalidFormatterError(ValueError):
    """Deprecated: Use :exc:`papis.plugin.InvalidPluginTypeError` instead."""


class FormatFailedError(Exception):
    """An exception that is thrown when a format pattern fails to be interpolated.

    This can happen due to lack of data (e.g. missing fields in the document)
    or invalid format patterns (e.g. passed to the wrong formatter).
    """


def unescape(fmt: str) -> str:
    return fmt.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")


class Formatter:
    """A generic formatter that works on templated strings using a document."""

    #: A name for the formatter.
    name: ClassVar[str]

    @cached_property
    def default_doc_name(self) -> str:
        from papis.config import getstring
        return getstring("format-doc-name")

    def format(self,
               fmt: str,
               doc: "DocumentLike",
               doc_key: str = "",
               additional: dict[str, Any] | None = None,
               default: str | None = None) -> str:
        """
        :param fmt: a format pattern understood by the formatter.
        :param doc: an object convertible to a document.
        :param doc_key: the name of the document in the format pattern. By
            default, this falls back to :confval:`format-doc-name`.
        :param default: an optional pattern to use as a default value if the
            formatting fails. If no default is given, a
            :exc:`~papis.format.FormatFailedError` will be raised.
        :param additional: a :class:`dict` of additional entries to pass to the
            formatter.

        :returns: a string with all the replacement fields filled in.
        """
        raise NotImplementedError(type(self).__name__)


def get_available_formatters() -> list[str]:
    """Get a list of all the available formatter plugins."""
    from papis.plugin import get_plugin_names
    return get_plugin_names(FORMATTER_NAMESPACE_NAME)


def get_formatter_by_name(name: str) -> Formatter:
    """Initialize and return a formatter plugin.

    :param name: the name of the desired formatter.
    """

    from papis.plugin import (
        InvalidPluginTypeError,
        PluginNotFoundError,
        get_plugin_by_name,
    )

    cls = get_plugin_by_name(FORMATTER_NAMESPACE_NAME, name)
    if cls is None:
        raise PluginNotFoundError(FORMATTER_NAMESPACE_NAME, name)

    f = cls()
    if not isinstance(f, Formatter):
        raise InvalidPluginTypeError(FORMATTER_NAMESPACE_NAME, name)

    return f


def get_cached_formatter(name: str | None = None) -> Formatter:
    """A cached variant of :func:`get_formatter_by_name`.

    :param name: the name of the desired formatter, by default this uses
        the value of :confval:`formatter`.
    """

    if name is None:
        from papis.config import getstring
        name = getstring("formatter")

    f: Formatter | None = FORMATTER_CACHE.get(name)
    if f is None:
        FORMATTER_CACHE[name] = f = get_formatter_by_name(name)
        logger.debug("Using '%s' formatter.", name)

    return f


def format(fmt: "AnyString",
           doc: "DocumentLike",
           doc_key: str = "",
           additional: dict[str, Any] | None = None,
           default: str | None = None) -> str:
    """Format a string using the selected formatter.

    This is the user-facing function that should be called when formatting a
    string. The formatters should not be called directly.

    Arguments match those of :meth:`Formatter.format`.
    """
    if isinstance(fmt, str):
        from papis.strings import FormatPattern
        fmt = FormatPattern(None, fmt)

    formatter = get_cached_formatter(fmt.formatter)
    return formatter.format(fmt.pattern, doc, doc_key=doc_key,
                            additional=additional,
                            default=default)


def __getattr__(name: str) -> Any:
    # NOTE: these are exported for backwards compatibility and should be removed
    # sometime in the future (papis v0.16 probably)

    if name == "PythonFormatter":
        from papis.format.python import PythonFormatter
        return PythonFormatter
    elif name == "Jinja2Formatter":
        from papis.format.jinja import Jinja2Formatter
        return Jinja2Formatter
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
