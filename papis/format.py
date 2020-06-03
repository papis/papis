import logging

import papis.config
import papis.plugin
import papis.document
from papis.document import Document 

LOGGER = logging.getLogger("format")

class Formater:
  def format(
        self,
        fmt: str, 
        doc: papis.document.Document,
        key: str = "") -> str:
    """Construct a string using a pythonic format string and a document.

    :param python_format: Python-like format string.
        (`see <
            https://docs.python.org/2/library/string.html#format-string-syntax
        >`_)
    :type  fmt: str
    :param doc: Papis document
    :type  document: papis.document.Document
    :returns: Formated string
    :rtype: str
    """
    doc_name = key or papis.config.getstring("format-doc-name")
    fdoc = Document()
    fdoc.update(doc)
    try:
        return fmt.format(**{doc_name: fdoc})
    except Exception as exception:
        return str(exception)

def _extension_name() -> str:
    return "papis.format"

def get_formater(name: str) -> Formater:
    """Get the formater named 'name' declared as a plugin"""
    formater = papis.plugin.get_extension_manager(
        _extension_name())[name].plugin  # type: Type[Picker[Option]]
    return formater

def format(
        fmt: str, 
        doc: papis.document.Document) -> str:

    name = papis.config.getstring("formater")
    try:
        formater = get_formater(name) 
    except KeyError:
        LOGGER.error("Invalid formater (%s)", name)
        LOGGER.error(
            "Registered formaters are: %s",
            papis.plugin.get_available_entrypoints(_extension_name()))
        return []
    else:
        return formater().format(fmt, doc)
