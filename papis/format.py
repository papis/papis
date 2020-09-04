import logging
from typing import Optional, Union, Any, Dict

import papis.config
import papis.plugin
import papis.document
from papis.document import Document


FormatDocType = Union[Document, Dict[str, Any]]
LOGGER = logging.getLogger("format")
_FORMATER = None  # type: Optional[Formater]


class Formater:
    def format(self,
               fmt: str,
               doc: FormatDocType,
               key: str = "") -> str:
        """
        :param fmt: Python-like format string.
        :type  fmt: str
        :param doc: Papis document
        :type  doc: FormatDocType
        :returns: Formated string
        :rtype: str
        """
        ...


class PythonFormater(Formater):
    """Construct a string using a pythonic format string and a document.
    You can activate this formater by setting ``formater = python``.
    """
    def format(self,
               fmt: str,
               doc: FormatDocType,
               key: str = "") -> str:
        doc_name = key or papis.config.getstring("format-doc-name")
        fdoc = Document()
        fdoc.update(doc)
        try:
            return fmt.format(**{doc_name: fdoc})
        except Exception as exception:
            return str(exception)


class Jinja2Formater(Formater):
    """Construct a Jinja2 formated string.
    You can activate this formater by setting ``formater = jinja2``.
    """

    def __init__(self) -> None:
        try:
            import jinja2
        except ImportError as exception:
            LOGGER.exception("""
            You're trying to format strings using jinja2
            Jinja2 is not installed by default, so just install it
                pip3 install jinja2
            """)
            str(exception)
        else:
            self.jinja2 = jinja2

    def format(self,
               fmt: str,
               doc: FormatDocType,
               key: str = "") -> str:
        doc_name = key or papis.config.getstring("format-doc-name")
        try:
            return str(self.jinja2.Template(fmt).render(**{doc_name: doc}))
        except Exception as exception:
            return str(exception)


def _extension_name() -> str:
    return "papis.format"


def get_formater() -> Formater:
    """Get the formater named 'name' declared as a plugin"""
    global _FORMATER
    if _FORMATER is None:
        name = papis.config.getstring("formater")
        try:
            _FORMATER = papis.plugin.get_extension_manager(
                _extension_name())[name].plugin()
        except KeyError:
            LOGGER.error("Invalid formater (%s)", name)
            raise Exception(
                "Registered formaters are: %s",
                papis.plugin.get_available_entrypoints(_extension_name()))
        LOGGER.debug("Getting {}".format(name))
    return _FORMATER


def format(fmt: str,
           doc: FormatDocType,
           key: str = "") -> str:
    formater = get_formater()
    return formater.format(fmt, doc, key)
