from string import Formatter as StringFormatter
from typing import Any, ClassVar

import papis.logging
from papis.document import Document, DocumentLike, describe, from_data
from papis.format import FormatFailedError, Formatter, unescape

logger = papis.logging.get_logger(__name__)


class _PythonStringFormatter(StringFormatter):
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

    def convert_field(self, value: Any, conversion: str | None) -> Any:
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
    (*str.format* based) format pattern.

    This formatter is named ``"python"`` and can be set using the
    :confval:`formatter` setting in the configuration file. The
    format pattern has access to the ``doc`` variable, that is always a
    :class:`papis.document.Document`. A pattern using this formatter can look
    like:

    .. code:: python

        "{doc[year]} - {doc[author_list][0][family]} - {doc[title]}"

    Note, however, that according to PEP 3101 some simple formatting is not
    possible. For example, the following is not allowed:

    .. code:: python

        "{doc[title].lower()}"

    and should be replaced with:

    .. code:: python

        "{doc[title]!l}"

    The following special conversions are implemented: "l" for :meth:`str.lower`,
    "u" for :meth:`str.upper`, "t" for :meth:`str.title`, "c" for
    :meth:`str.capitalize`, "y" that uses ``slugify`` (through
    :func:`papis.paths.normalize_path`). Additionally, the following
    syntax is available to select subsets from a string:

    .. code:: python

        "{doc[title]:1.3S}"

    which will select the ``words[1:3]`` from the title (words are split by
    single spaces).
    """

    name: ClassVar[str] = "python"
    psf = _PythonStringFormatter()

    def format(self,
               fmt: str,
               doc: DocumentLike,
               doc_key: str = "",
               additional: dict[str, Any] | None = None,
               default: str | None = None) -> str:
        if additional is None:
            additional = {}

        fmt = unescape(fmt)
        if not isinstance(doc, Document):
            doc = from_data(doc)

        doc_name = doc_key or self.default_doc_name

        try:
            return self.psf.format(fmt, **{doc_name: doc}, **additional)
        except Exception as exc:
            if default is not None:
                logger.warning("Could not format pattern '%s' for document '%s'",
                               fmt, describe(doc), exc_info=exc)
                return default
            else:
                raise FormatFailedError(fmt) from exc
