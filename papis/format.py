from typing import Any, Dict, Optional, Union

import papis.config
import papis.plugin
import papis.document
import papis.logging
from papis.document import Document

logger = papis.logging.get_logger(__name__)

FormatDocType = Union[Document, Dict[str, Any]]
_FORMATER = None  # type: Optional[Formater]


class InvalidFormaterError(ValueError):
    pass


InvalidFormatterValue = InvalidFormaterError


def unescape(fmt: str) -> str:
    return fmt.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")


class Formater:
    def __init__(self) -> None:
        self.default_doc_name = papis.config.getstring("format-doc-name")

    def format(self,
               fmt: str,
               doc: FormatDocType,
               doc_key: str = "",
               additional: Optional[Dict[str, Any]] = None) -> str:
        """
        :param fmt: a format string understood by the formater.
        :param doc: an object convertible to a document.
        :param doc_key: the name of the document in the format string. By
            default, this falls back to ``"format-doc-name"``.
        :param additional: a :class:`dict` of additional entries to pass to the
            formater.

        :returns: a string with all the replacement fields filled in.
        """
        raise NotImplementedError(type(self).__name__)


class PythonFormater(Formater):
    """Construct a string using a `PEP 3101 <https://peps.python.org/pep-3101/>`__
    (`str.format` based) format string.

    This formater is named ``"python"`` and can be set using the ``formater``
    setting in the configuration file (see :ref:`general-settings`).
    """

    def format(self,
               fmt: str,
               doc: FormatDocType,
               doc_key: str = "",
               additional: Optional[Dict[str, Any]] = None) -> str:
        if additional is None:
            additional = {}

        fmt = unescape(fmt)
        if not isinstance(doc, papis.document.Document):
            doc = papis.document.from_data(doc)

        doc_name = doc_key or self.default_doc_name
        try:
            return fmt.format(**{doc_name: doc}, **additional)
        except Exception as exc:
            return "{}: {}".format(type(exc).__name__, exc)


class Jinja2Formater(Formater):
    """Construct a string using `Jinja2 <https://palletsprojects.com/p/jinja/>`__
    templates.

    This formater is named ``"jinja2"`` and can be set using the ``formater``
    setting in the configuration file (see :ref:`general-settings`).
    """

    def __init__(self) -> None:
        super().__init__()

        try:
            import jinja2       # noqa: F401
        except ImportError as exc:
            logger.error(
                "The 'jinja2' formater requires the 'jinja' library. "
                "To use this functionality install it using e.g. "
                "'pip install jinja2'.", exc_info=exc)
            raise exc

    def format(self,
               fmt: str,
               doc: FormatDocType,
               doc_key: str = "",
               additional: Optional[Dict[str, Any]] = None) -> str:
        if additional is None:
            additional = {}

        from jinja2 import Template

        fmt = unescape(fmt)
        if not isinstance(doc, papis.document.Document):
            doc = papis.document.from_data(doc)

        doc_name = doc_key or self.default_doc_name
        try:
            return str(Template(fmt).render(**{doc_name: doc}, **additional))
        except Exception as exc:
            return "{}: {}".format(type(exc).__name__, exc)


def _extension_name() -> str:
    return "papis.format"


def get_formater(name: Optional[str] = None) -> Formater:
    """Initialize a formater plugin.

    Note that the formater is cached and all subsequence calls to this function
    will return the same formater.

    :param name: the name of the desired formater.
    """
    global _FORMATER

    if _FORMATER is None:
        mgr = papis.plugin.get_extension_manager(_extension_name())

        if name is None:
            name = papis.config.getstring("formater")

        try:
            _FORMATER = mgr[name].plugin()
        except Exception as exc:
            entrypoints = papis.plugin.get_available_entrypoints(_extension_name())
            logger.error("Invalid formater '%s'. Registered formaters are '%s'.",
                         name, "', '".join(entrypoints), exc_info=exc)
            raise InvalidFormaterError("Invalid formater: '{}'".format(name))

        logger.debug("Using '%s' formater.", name)

    return _FORMATER


def format(fmt: str,
           doc: FormatDocType,
           doc_key: str = "",
           additional: Optional[Dict[str, Any]] = None) -> str:
    formater = get_formater()
    return formater.format(fmt, doc, doc_key=doc_key, additional=additional)
