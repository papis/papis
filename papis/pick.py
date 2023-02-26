import os
import functools
from abc import ABC, abstractmethod
from typing import Callable, TypeVar, Generic, Sequence, Type

import papis.config
import papis.document
import papis.plugin
import papis.logging

logger = papis.logging.get_logger(__name__)

T = TypeVar("T")
Option = TypeVar("Option")


class Picker(ABC, Generic[T]):

    @abstractmethod
    def __call__(
            self,
            items: Sequence[T],
            header_filter: Callable[[T], str],
            match_filter: Callable[[T], str],
            default_index: int = 0
            ) -> Sequence[T]:
        pass


def _extension_name() -> str:
    return "papis.picker"


def get_picker(name: str) -> Type[Picker[Option]]:
    """Get the picker named 'name' declared as a plugin"""
    picker = papis.plugin.get_extension_manager(
        _extension_name())[name].plugin  # type: Type[Picker[Option]]
    return picker


def pick(
        options: Sequence[Option],
        default_index: int = 0,
        header_filter: Callable[[Option], str] = str,
        match_filter: Callable[[Option], str] = str) -> Sequence[Option]:

    name = papis.config.getstring("picktool")
    try:
        picker = get_picker(name)  # type: Type[Picker[Option]]
    except KeyError:
        entrypoints = papis.plugin.get_available_entrypoints(_extension_name())
        logger.error(
            "Invalid picker: '%s'. Registered pickers are '%s'.",
            name, "', '".join(entrypoints))
        return []
    else:
        return picker()(options,
                        header_filter,
                        match_filter,
                        default_index)


def pick_doc(
        documents: Sequence[papis.document.Document]
        ) -> Sequence[papis.document.Document]:
    """Pick a document from documents with the correct formatting

    :documents: List of documents
    :returns: Document

    """
    header_format_path = papis.config.get("header-format-file")
    if header_format_path is not None:
        with open(os.path.expanduser(header_format_path)) as _fd:
            header_format = _fd.read().rstrip()
    else:
        header_format = papis.config.getstring("header-format")
    match_format = papis.config.getstring("match-format")
    header_filter = functools.partial(papis.format.format, header_format)
    match_filter = functools.partial(papis.format.format, match_format)
    return pick(documents,
                header_filter=header_filter,
                match_filter=match_filter)


def pick_subfolder_from_lib(lib: str) -> Sequence[str]:
    """Pick a subfolder from all existings subfolders in library

    Args:
        lib (str): Library to search for subfolders

    Returns:
        Sequence[str]: Paths to subfolder
    """
    import papis.api

    documents = papis.api.get_all_documents_in_lib(lib)

    # find all folders containing documents
    folders = [os.path.dirname(str(d.get_main_folder())) for d in documents]
    folders.append(*papis.config.get_lib_dirs())

    # remove duplicates and sort paths
    folders = sorted([*set(folders)])

    return pick(folders)
