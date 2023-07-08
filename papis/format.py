from typing import Any, Dict, Optional

import papis.config
import papis.plugin
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)

FORMATER: Optional["Formater"] = None

#: The entry point name for formater plugins.
FORMATER_EXTENSION_NAME = "papis.format"


class InvalidFormaterError(ValueError):
    """An exception that is thrown when an invalid formater is selected."""


def unescape(fmt: str) -> str:
    return fmt.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")


class Formater:
    """A generic formatter that works on templated strings using a document."""

    def __init__(self) -> None:
        self.default_doc_name = papis.config.getstring("format-doc-name")

    def format(self,
               fmt: str,
               doc: papis.document.DocumentLike,
               doc_key: str = "",
               additional: Optional[Dict[str, Any]] = None) -> str:
        """
        :param fmt: a format string understood by the formater.
        :param doc: an object convertible to a document.
        :param doc_key: the name of the document in the format string. By
            default, this falls back to :ref:`config-settings-format-doc-name`.
        :param additional: a :class:`dict` of additional entries to pass to the
            formater.

        :returns: a string with all the replacement fields filled in.
        """
        raise NotImplementedError(type(self).__name__)


class PythonFormater(Formater):
    """Construct a string using a `PEP 3101 <https://peps.python.org/pep-3101/>`__
    (*str.format* based) format string.

    This formater is named ``"python"`` and can be set using the
    :ref:`config-settings-formater` setting in the configuration file.
    """

    def format(self,
               fmt: str,
               doc: papis.document.DocumentLike,
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
            logger.debug("Could not format string '%s' for document '%s'",
                         fmt, papis.document.describe(doc), exc_info=exc)

            return "{}: {}".format(type(exc).__name__, exc)


class Jinja2Formater(Formater):
    """Construct a string using `Jinja2 <https://palletsprojects.com/p/jinja/>`__
    templates.

    This formater is named ``"jinja2"`` and can be set using the
    :ref:`config-settings-formater` setting in the configuration file.
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
               doc: papis.document.DocumentLike,
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
            logger.debug("Could not format string '%s' for document '%s'",
                         fmt, papis.document.describe(doc), exc_info=exc)

            return "{}: {}".format(type(exc).__name__, exc)


def get_formater(name: Optional[str] = None) -> Formater:
    """Initialize and return a formater plugin.

    Note that the formater is cached and all subsequent calls to this function
    will return the same formater.

    :param name: the name of the desired formater, by default this uses
        the value of :ref:`config-settings-formater`.
    """
    global FORMATER

    if FORMATER is None:
        mgr = papis.plugin.get_extension_manager(FORMATER_EXTENSION_NAME)

        if name is None:
            name = papis.config.getstring("formater")

        try:
            FORMATER = mgr[name].plugin()
        except Exception as exc:
            entrypoints = (
                papis.plugin.get_available_entrypoints(FORMATER_EXTENSION_NAME))
            logger.error("Invalid formater '%s'. Registered formaters are '%s'.",
                         name, "', '".join(entrypoints), exc_info=exc)
            raise InvalidFormaterError("Invalid formater: '{}'".format(name))

        logger.debug("Using '%s' formater.", name)

    return FORMATER


def format(fmt: str,
           doc: papis.document.DocumentLike,
           doc_key: str = "",
           additional: Optional[Dict[str, Any]] = None) -> str:
    """Format a string using the selected formater.

    This is the user-facing function that should be called when formating a
    string. The formaters should not be called directly.
    """
    formater = get_formater()
    return formater.format(fmt, doc, doc_key=doc_key, additional=additional)
