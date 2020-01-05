import logging
import os
import sys
import functools
from typing import List, Callable, Optional

import papis.config
import papis.document
from papis.tui.app import Picker, Option
import papis.plugin

Filter = Callable[[Option], str]

LOGGER = logging.getLogger("pick")

PickerType = Callable[[List[Option], int, Filter[Option], Filter[Option]],
                      Optional[Option]]


def _extension_name() -> str:
    return "papis.picker"


def papis_pick(
        options: List[Option],
        default_index: int = 0,
        header_filter: Filter[Option] = str,
        match_filter: Filter[Option] = str) -> Optional[Option]:

    if len(options) == 0:
        return None
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


def get_picker(name: str) -> PickerType[Option]:
    """Get the picker named 'name' declared as a plugin"""
    picker = papis.plugin.get_extension_manager(
        _extension_name())[name].plugin  # type: PickerType[Option]
    return picker


def pick(
        options: List[Option],
        default_index: int = 0,
        header_filter: Filter[Option] = str,
        match_filter: Filter[Option] = str) -> Optional[Option]:

    name = papis.config.getstring("picktool")
    try:
        picker = get_picker(name)  # type: PickerType[Option]
    except KeyError:
        LOGGER.error("Invalid picker (%s)", name)
        LOGGER.error(
            "Registered pickers are: %s",
            papis.plugin.get_available_entrypoints(_extension_name()))
        return None
    else:
        return picker(options,
                      default_index,
                      header_filter,
                      match_filter)


def pick_doc(documents: List[papis.document.Document]
             ) -> Optional[papis.document.Document]:
    """Pick a document from documents with the correct formatting

    :documents: List of documents
    :returns: Document

    """
    header_format_path = papis.config.get('header-format-file')
    if header_format_path is not None:
        with open(os.path.expanduser(header_format_path)) as _fd:
            header_format = _fd.read()
    else:
        header_format = papis.config.getstring("header-format")
    match_format = papis.config.getstring("match-format")
    header_filter = functools.partial(papis.document.format_doc, header_format)
    match_filter = functools.partial(papis.document.format_doc, match_format)
    return pick(documents,
                header_filter=header_filter,
                match_filter=match_filter)
