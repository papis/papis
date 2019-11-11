import logging
import os
import sys
import papis.config
import papis.document
from papis.tui.app import Picker
import papis.plugin

from typing import Sequence, Any, Callable
_filter_type = Callable[[Any], Any]
_option_type = Sequence[Any]

logger = logging.getLogger("pick")


def _extension_name() -> str:
    return "papis.picker"


def papis_pick(options: _option_type, default_index: int = 0,
        header_filter: _filter_type = lambda x: x,
        match_filter: _filter_type = lambda x: x) -> Any:
    if len(options) == 0:
        return ""
    if len(options) == 1:
        return options[0]

    # patch stdout to stderr if the output is not a tty (terminal)
    oldstdout = sys.stdout
    if not sys.stdout.isatty():
        sys.stdout = sys.stderr
        sys.__stdout__ = sys.stderr

    picker = Picker(
        options,
        default_index,
        header_filter,
        match_filter
    )
    picker.run()
    result = picker.options_list.get_selection()

    # restore the stdout to normality
    sys.stdout = oldstdout
    sys.__stdout__ = oldstdout

    return result


def pick(options: _option_type, default_index: int = 0,
        header_filter: _filter_type = lambda x: x,
        match_filter: _filter_type = lambda x: x) -> Any:
    """Construct and start a :class:`Picker <Picker>`.
    """
    name = papis.config.get("picktool")
    try:
        picker = papis.plugin.get_extension_manager(
                        _extension_name())[name].plugin
    except KeyError:
        logger.error("Invalid picker ({0})".format(name))
        logger.error(
            "Registered pickers are: {0}"
            .format(papis.plugin.get_available_entrypoints(_extension_name())))
        return []
    else:
        return picker(
            options,
            default_index=default_index,
            header_filter=header_filter,
            match_filter=match_filter)


def pick_doc(documents: Sequence[papis.document.Document]
        ) -> papis.document.Document:
    """Pick a document from documents with the correct formatting

    :documents: List of documents
    :returns: Document

    """
    header_format_path = papis.config.get('header-format-file')
    if header_format_path is not None:
        with open(os.path.expanduser(header_format_path)) as fd:
            header_format = fd.read()
    else:
        header_format = papis.config.getstring("header-format")
    match_format = papis.config.getstring("match-format")
    pick_config = dict(
        header_filter=lambda x: papis.utils.format_doc(header_format, x),
        match_filter=lambda x: papis.utils.format_doc(match_format, x))
    return pick(documents, **pick_config)
