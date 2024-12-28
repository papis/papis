import string
from typing import Any, ClassVar, Dict, List, Optional

import papis.config
import papis.plugin
import papis.strings
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)

FORMATTER: Dict[str, "Formatter"] = {}

#: The entry point name for formatter plugins.
FORMATTER_EXTENSION_NAME = "papis.format"


class InvalidFormatterError(ValueError):
    """An exception that is thrown when an invalid formatter is selected."""


class FormatFailedError(Exception):
    """An exception that is thrown when a format string fails to be interpolated.

    This can happen due to lack of data (e.g. missing fields in the document)
    or invalid format strings (e.g. passed to the wrong formatter).
    """


def unescape(fmt: str) -> str:
    return fmt.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")


class Formatter:
    """A generic formatter that works on templated strings using a document."""

    #: A name for the formatter.
    name: ClassVar[str]

    def __init__(self) -> None:
        self.default_doc_name = papis.config.getstring("format-doc-name")

    def format(self,
               fmt: str,
               doc: papis.document.DocumentLike,
               doc_key: str = "",
               additional: Optional[Dict[str, Any]] = None,
               default: Optional[str] = None) -> str:
        """
        :param fmt: a format string understood by the formatter.
        :param doc: an object convertible to a document.
        :param doc_key: the name of the document in the format string. By
            default, this falls back to :confval:`format-doc-name`.
        :param default: an optional string to use as a default value if the
            formatting fails. If no default is given, a :exc:`FormatFailedError`
            will be raised.
        :param additional: a :class:`dict` of additional entries to pass to the
            formatter.

        :returns: a string with all the replacement fields filled in.
        """
        raise NotImplementedError(type(self).__name__)


class _PythonStringFormatter(string.Formatter):
    # https://docs.python.org/3/library/string.html#format-specification-mini-language
    # NOTE: Known conversions are:
    #   !s      -> calls str(value)
    #   !r      -> calls repr(value)
    #   !a      -> calls ascii(value)

    def format_field(self, value: Any, format_spec: str) -> Any:
        if format_spec and format_spec[-1] == "S":
            format_spec = format_spec[:-1]
            try:
                if "." in format_spec:
                    start, end = format_spec.split(".")
                    start = start if start else "0"
                else:
                    start, end = "0", format_spec

                istart, iend = int(start), int(end)
            except ValueError:
                raise ValueError(f"Invalid format specifier '{format_spec}'") from None

            if isinstance(value, str):
                return " ".join(value.split(" ")[istart:iend])
            else:
                raise ValueError(
                    f"Unknown format code 'S' for type '{type(value).__name__}'")

        return super().format_field(value, format_spec)

    def convert_field(self, value: Any, conversion: Optional[str]) -> Any:
        if conversion == "l":
            return str(value).lower()
        if conversion == "u":
            return str(value).upper()
        if conversion == "t":
            return str(value).title()
        if conversion == "c":
            return str(value).capitalize()
        if conversion == "y":
            from papis.paths import normalize_path
            return normalize_path(str(value))

        return super().convert_field(value, conversion)


class PythonFormatter(Formatter):
    """Construct a string using a `PEP 3101 <https://peps.python.org/pep-3101/>`__
    (*str.format* based) format string.

    This formatter is named ``"python"`` and can be set using the
    :confval:`formatter` setting in the configuration file. The
    formatted string has access to the ``doc`` variable, that is always a
    :class:`papis.document.Document`. A string using this formatter can look
    like

    .. code:: python

        "{doc[year]} - {doc[author_list][0][family]} - {doc[title]}"

    Note, however, that according to PEP 3101 some simple formatting is not
    possible. For example, the following is not allowed

    .. code:: python

        "{doc[title].lower()}"

    and should be replaced with

    .. code:: python

        "{doc[title]!l}"

    The following special conversions are implemented: "l" for :meth:`str.lower`,
    "u" for :meth:`str.upper`, "t" for :meth:`str.title`, "c" for
    :meth:`str.capitalize`, "y" that uses ``slugify`` (through
    :func:`papis.paths.normalize_path`). Additionally, the following
    syntax is available to select subsets from a string

    .. code:: python

        "{doc[title]:1.3S}"

    which will select the ``words[1:3]`` from the title (words are split by
    single spaces).
    """

    name: ClassVar[str] = "python"
    psf = _PythonStringFormatter()

    def format(self,
               fmt: str,
               doc: papis.document.DocumentLike,
               doc_key: str = "",
               additional: Optional[Dict[str, Any]] = None,
               default: Optional[str] = None) -> str:
        if additional is None:
            additional = {}

        fmt = unescape(fmt)
        if not isinstance(doc, papis.document.Document):
            doc = papis.document.from_data(doc)

        doc_name = doc_key or self.default_doc_name

        try:
            return self.psf.format(fmt, **{doc_name: doc}, **additional)
        except Exception as exc:
            if default is not None:
                logger.warning("Could not format string '%s' for document '%s'",
                               fmt, papis.document.describe(doc), exc_info=exc)
                return default
            else:
                raise FormatFailedError(fmt) from exc


class Jinja2Formatter(Formatter):
    """Construct a string using `Jinja2 <https://palletsprojects.com/p/jinja/>`__
    templates.

    This formatter is named ``"jinja2"`` and can be set using the
    :confval:`formatter` setting in the configuration file. The
    formatted string has access to the ``doc`` variable, that is always a
    :class:`papis.document.Document`. A string using this formatter can look
    like

    .. code:: python

        "{{ doc.year }} - {{ doc.author_list[0].family }} - {{ doc.title }}"

    This formatter supports the whole range of Jinja2 control structures and
    `filters <https://jinja.palletsprojects.com/en/3.1.x/templates/#filters>`__
    so more advanced string processing is possible. For example, we can titlecase
    the title using

    .. code:: python

        "{{ doc.title | title }}"

    or give a default value if a key is missing in the document using

    .. code:: python

        "{{ doc.isbn | default('ISBN-NONE', true) }}"
    """

    name: ClassVar[str] = "jinja2"

    env: ClassVar[Any] = None
    """The ``jinja2`` Environment used by the formatter. This should be obtained
    with :meth:`~Jinja2Formatter.get_environment()` (cached) and modified as
    required (e.g. by adding filters).
    """

    def __init__(self) -> None:
        super().__init__()

        try:
            import jinja2  # noqa: F401
        except ImportError as exc:
            logger.error(
                "The 'jinja2' formatter requires the 'jinja2' library. "
                "To use this functionality install it using e.g. "
                "'pip install jinja2'.", exc_info=exc)
            raise exc

    @classmethod
    def get_environment(cls, *, force: bool = False) -> Any:
        if cls.env is None or force:
            from jinja2 import Environment

            # NOTE: this will kindly autoescape apostrophes otherwise
            env = Environment(autoescape=False)
            env.shared = True
            cls.env = env

        return cls.env

    def format(self,
               fmt: str,
               doc: papis.document.DocumentLike,
               doc_key: str = "",
               additional: Optional[Dict[str, Any]] = None,
               default: Optional[str] = None) -> str:
        if additional is None:
            additional = {}

        fmt = unescape(fmt)
        if not isinstance(doc, papis.document.Document):
            doc = papis.document.from_data(doc)

        doc_name = doc_key or self.default_doc_name
        env = self.get_environment()

        try:
            return str(env.from_string(fmt).render(**{doc_name: doc}, **additional))
        except Exception as exc:
            if default is not None:
                logger.warning("Could not format string '%s' for document '%s'",
                               fmt, papis.document.describe(doc), exc_info=exc)
                return default
            else:
                raise FormatFailedError(fmt) from exc


def get_available_formatters() -> List[str]:
    """Get a list of all the available formatter plugins."""
    return papis.plugin.get_available_entrypoints(FORMATTER_EXTENSION_NAME)


def get_default_formatter() -> str:
    """Get the default formatter from :confval:`formatter`."""
    from papis.defaults import NOT_SET

    # FIXME: remove this special handling when we don't need to support
    # the deprecated 'formater' configuration setting
    value = papis.config.get("formater")
    if value is NOT_SET:
        name = papis.config.getstring("formatter")
    else:
        logger.warning("The configuration option 'formater' is deprecated. "
                       "Use 'formatter' instead.")
        name = str(value)

    return name


def get_formatter(name: Optional[str] = None) -> Formatter:
    """Initialize and return a formatter plugin.

    Note that the formatter is cached and all subsequent calls to this function
    will return the same formatter.

    :param name: the name of the desired formatter, by default this uses
        the value of :confval:`formatter`.
    """
    global FORMATTER

    if name is None:
        name = get_default_formatter()

    f = FORMATTER.get(name)
    if f is None:
        mgr = papis.plugin.get_extension_manager(FORMATTER_EXTENSION_NAME)
        try:
            f = mgr[name].plugin()
        except Exception as exc:
            logger.error("Invalid formatter '%s'. Registered formatters are '%s'.",
                         name, "', '".join(get_available_formatters()), exc_info=exc)
            raise InvalidFormatterError(f"Invalid formatter: '{name}'") from None

        FORMATTER[name] = f
        logger.debug("Using '%s' formatter.", name)

    return f


def format(fmt: papis.strings.AnyString,
           doc: papis.document.DocumentLike,
           doc_key: str = "",
           additional: Optional[Dict[str, Any]] = None,
           default: Optional[str] = None) -> str:
    """Format a string using the selected formatter.

    This is the user-facing function that should be called when formatting a
    string. The formatters should not be called directly.

    Arguments match those of :meth:`Formatter.format`.
    """
    if isinstance(fmt, str):
        fmt = papis.strings.FormattedString(None, fmt)

    formatter = get_formatter(fmt.formatter)
    return formatter.format(fmt.value, doc, doc_key=doc_key,
                            additional=additional,
                            default=default)


_DEPRECATIONS: Dict[str, Any] = {
    "InvalidFormaterError": InvalidFormatterError,
    "Formater": Formatter,
    "PythonFormater": PythonFormatter,
    "Jinja2Formater": Jinja2Formatter,
    "get_formater": get_formatter,
}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATIONS:
        from warnings import warn
        warn(f"{name!r} is deprecated, use {_DEPRECATIONS[name].__name__!r} instead",
             DeprecationWarning, stacklevel=2)
        return _DEPRECATIONS[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
