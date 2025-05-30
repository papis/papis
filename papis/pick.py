import os
from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar, Generic, Sequence, Type, Optional, List

import papis.config
import papis.document
import papis.plugin
import papis.logging

logger = papis.logging.get_logger(__name__)

#: Name of the entry points for :class:`Picker` plugins.
PICKER_EXTENSION_NAME = "papis.picker"

#: Invariant :class:`~typing.TypeVar` with no bounds.
T = TypeVar("T")


class Picker(ABC, Generic[T]):
    """An interface used to select items from a list.

    .. automethod:: __call__
    """

    @abstractmethod
    def __call__(
            self,
            items: Sequence[T],
            header_filter: Callable[[T], str],
            match_filter: Callable[[T], str],
            default_index: int = 0
            ) -> List[T]:
        """
        :arg items: a sequence of items from which to pick a subset.
        :arg header_filter: (optional) a callable that takes an item from *items*
            and returns a string representation shown to the user.
        :arg match_filter: (optional) a callable that takes an item from *items*
            and returns a string representation that is used when searching or
            filtering the items.
        :arg default_index: (optional) sets the selected item when the picker
            is first shown to the user.

        :returns: a subset of *items* that were picked.
        """


def get_picker(name: str) -> Type[Picker[Any]]:
    """Get a picker by its plugin name.

    :arg name: the name of an entrypoint to load a :class:`Picker` plugin from.
    :returns: a :class:`Picker` subclass implemented in the plugin.
    """
    picker: Type[Picker[Any]] = (
        papis.plugin.get_extension_manager(PICKER_EXTENSION_NAME)[name].plugin
    )

    return picker


def pick(items: Sequence[T],
         header_filter: Callable[[T], str] = str,
         match_filter: Callable[[T], str] = str,
         default_index: int = 0) -> List[T]:
    """Load a :class:`Picker` plugin and select a subset of *items*.

    The arguments to this function match those of :meth:`Picker.__call__`. The
    specific picker is chosen through the :confval:`picktool`
    configuration option.

    :returns: a subset of *items* that were picked.
    """

    name = papis.config.getstring("picktool")
    try:
        picker: Type[Picker[T]] = get_picker(name)
    except KeyError:
        entrypoints = papis.plugin.get_available_entrypoints(PICKER_EXTENSION_NAME)
        logger.error(
            "Invalid picker: '%s'. Registered pickers are '%s'.",
            name, "', '".join(entrypoints))
        return []
    else:
        return picker()(items,
                        header_filter,
                        match_filter,
                        default_index)


def pick_doc(
        documents: Sequence[papis.document.Document]
        ) -> List[papis.document.Document]:
    """Pick from a sequence of *documents* using :func:`pick`.

    This function uses the :confval:`header-format-file` setting
    or, if not available, the :confval:`header-format` setting
    to construct a *header_filter* for the picker. It also uses the configuration
    setting :confval:`match-format` to construct a *match_filter*.

    :arg documents: a sequence of documents.
    :returns: a subset of *documents* that was picked.
    """
    from papis.strings import FormattedString

    header_format_path = papis.config.get("header-format-file")
    if header_format_path is not None:
        with open(os.path.expanduser(header_format_path), encoding="utf-8") as fd:
            header_format = FormattedString(None, fd.read().rstrip())
    else:
        header_format = papis.config.getformattedstring("header-format")
    match_format = papis.config.getformattedstring("match-format")

    from functools import partial

    header_filter = partial(papis.format.format, header_format)
    match_filter = partial(papis.format.format, match_format)

    return pick(documents,
                header_filter=header_filter,
                match_filter=match_filter)


def pick_subfolder_from_lib(lib: str) -> List[str]:
    """Pick subfolders from all existing subfolders in *lib*.

    Note that this includes document folders in *lib* as well nested library
    folders.

    :arg lib: the name of an existing library to search in.
    :returns: a subset of the subfolders in the library.
    """
    import papis.api
    documents = papis.api.get_all_documents_in_lib(lib)

    # get all document directories
    folders = [os.path.dirname(str(d.get_main_folder())) for d in documents]
    # get all library directories
    folders.append(*papis.config.get_lib_dirs())
    # remove duplicates and sort paths
    folders = sorted(set(folders))

    return pick(folders)


def pick_library(libs: Optional[List[str]] = None) -> List[str]:
    """Pick a library from the current configuration.

    :arg libs: a list of libraries to pick from.
    """
    if libs is None:
        libs = papis.api.get_libraries()

    header_format = papis.config.getformattedstring("library-header-format")

    def header_filter(lib: str) -> str:
        library = papis.config.get_lib_from_name(lib)
        return papis.format.format(header_format, {
            "name": library.name,
            "dir": library.paths[0],
            "paths": library.paths
            }, doc_key="library")

    return pick(libs,
                header_filter=header_filter,
                match_filter=str)
