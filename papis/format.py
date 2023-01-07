from typing import Any, Dict, Optional, Union

import papis.config
import papis.plugin
import papis.document
import papis.logging
from papis.document import Document

logger = papis.logging.get_logger(__name__)

FormatDocType = Union[Document, Dict[str, Any]]
_FORMATER = None  # type: Optional[Formater]


class InvalidFormatterValue(Exception):
    pass


def escape(fmt: str) -> str:
    # NOTE: this escapes '\n' and '\t' characters in the string so that they
    # get printed properly when doing the 'fmt.format' below

    import codecs
    try:
        return codecs.decode(fmt, "unicode-escape")
    except ValueError:
        return fmt


class Formater:
    def format(self,
               fmt: str,
               doc: FormatDocType,
               doc_key: str = "",
               additional: Optional[Dict[str, Any]] = None) -> str:
        """
        :param fmt: Python-like format string.
        :param doc: Papis document
        :param doc_key: Name of the document in the format string
        :param additional: Additional named keys available to the format string
        :returns: Formated string
        """
        raise NotImplementedError


class PythonFormater(Formater):
    """Construct a string using a pythonic format string and a document.
    You can activate this formatter by setting ``formater = python``.
    """
    def format(self,
               fmt: str,
               doc: FormatDocType,
               doc_key: str = "",
               additional: Optional[Dict[str, Any]] = None) -> str:
        if additional is None:
            additional = {}

        fmt = escape(fmt)
        doc = papis.document.from_data(doc)

        doc_name = doc_key or papis.config.getstring("format-doc-name")
        try:
            return fmt.format(**{doc_name: doc}, **additional)
        except Exception as exc:
            return "{}: {}".format(type(exc).__name__, exc)


class Jinja2Formater(Formater):
    """Construct a Jinja2 formated string.
    You can activate this formatter by setting ``formater = jinja2``.
    """

    def __init__(self) -> None:
        try:
            import jinja2
        except ImportError:
            logger.exception("""
            You're trying to format strings using jinja2
            Jinja2 is not installed by default, so just install it
                pip3 install jinja2
            """)
        else:
            self.jinja2 = jinja2

    def format(self,
               fmt: str,
               doc: FormatDocType,
               doc_key: str = "",
               additional: Optional[Dict[str, Any]] = None) -> str:
        if additional is None:
            additional = {}

        fmt = escape(fmt)
        doc = papis.document.from_data(doc)

        doc_name = doc_key or papis.config.getstring("format-doc-name")
        try:
            return str(self.jinja2
                           .Template(fmt)
                           .render(**{doc_name: doc}, **additional))
        except Exception as exception:
            return str(exception)


def _extension_name() -> str:
    return "papis.format"


def get_formater() -> Formater:
    """Get the formatter named 'name' declared as a plugin"""
    global _FORMATER
    if _FORMATER is None:
        name = papis.config.getstring("formater")
        try:
            _FORMATER = papis.plugin.get_extension_manager(
                _extension_name())[name].plugin()
        except KeyError:
            logger.error("Invalid formatter: %s", name)
            raise InvalidFormatterValue(
                "Registered formatters are: %s",
                papis.plugin.get_available_entrypoints(_extension_name()))
        logger.debug("Getting %s", name)

    return _FORMATER


def format(fmt: str,
           doc: FormatDocType,
           doc_key: str = "",
           additional: Optional[Dict[str, Any]] = None) -> str:
    formater = get_formater()
    return formater.format(fmt, doc, doc_key=doc_key, additional=additional)
