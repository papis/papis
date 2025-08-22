import os
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import papis.config
import papis.logging

if TYPE_CHECKING:
    import papis.document
    import papis.strings

logger = papis.logging.get_logger(__name__)

#: Name of the entry point namespace for :class:`Picker` plugins.
PICKER_NAMESPACE_NAME = "papis.picker"

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
            ) -> list[T]:
        """
        :arg items: a sequence of items from which to pick a subset.
        :arg header_filter: a callable that takes an item from *items*
            and returns a string representation shown to the user.
        :arg match_filter: a callable that takes an item from *items*
            and returns a string representation that is used when searching or
            filtering the items.
        :arg default_index: sets the selected item when the picker is first
            shown to the user.

        :returns: a subset of *items* that were picked.
        """


def get_available_pickers() -> list[str]:
    """Gets all registered pickers."""
    from papis.plugin import get_plugin_names

    return get_plugin_names(PICKER_NAMESPACE_NAME)


def get_picker_by_name(name: str) -> type[Picker[Any]]:
    """Get a picker by its plugin name.

    :arg name: the name of an entrypoint to load a :class:`Picker` plugin from.
    :returns: a :class:`Picker` subclass implemented in the plugin.
    """
    from papis.plugin import InvalidPluginTypeError, get_plugin_by_name

    cls = get_plugin_by_name(PICKER_NAMESPACE_NAME, name)
    if cls is None:
        logger.error("Failed to load picker '%s'. "
                     "Falling back to default 'papis' picker!", name)
        cls = get_plugin_by_name(PICKER_NAMESPACE_NAME, "papis")

    if cls is None or not issubclass(cls, Picker):
        raise InvalidPluginTypeError(PICKER_NAMESPACE_NAME, name)

    return cls  # type: ignore[no-any-return]


def get_picker(name: str) -> type[Picker[Any]]:
    from warnings import warn

    warn("'papis.pick.get_picker' is deprecated and will be removed in "
         "Papis v0.16. Use 'papis.pick.get_picker_by_name' instead.",
         DeprecationWarning, stacklevel=2)

    return get_picker_by_name(name)


def pick(items: Sequence[T],
         header_filter: Callable[[T], str] = str,
         match_filter: Callable[[T], str] = str,
         default_index: int = 0, *,
         picktool: str | None = None) -> list[T]:
    """Load a :class:`Picker` plugin and select a subset of *items*.

    The arguments to this function match those of :meth:`Picker.__call__`. The
    specific picker is chosen through the :confval:`picktool` configuration
    option.

    :returns: a subset of *items* that were picked.
    """
    from papis.plugin import PluginError

    if picktool is None:
        picktool = papis.config.getstring("picktool")

    try:
        picker: type[Picker[T]] = get_picker_by_name(picktool)
    except PluginError as exc:
        logger.error("Failed to load picker '%s'.", picktool, exc_info=exc)
        return []

    return picker()(items,
                    header_filter,
                    match_filter,
                    default_index)


def pick_doc(documents: Sequence["papis.document.Document"], *,
             header_format_file: str | None = None,
             header_format: "papis.strings.AnyString | None" = None,
             match_format: "papis.strings.AnyString | None" = None,
             ) -> list["papis.document.Document"]:
    """Pick from a sequence of *documents* using :func:`pick`.

    This function uses the :confval:`header-format-file` setting or, if not
    available, the :confval:`header-format` setting to construct a
    *header_filter* for the picker. It also uses the configuration setting
    :confval:`match-format` to construct a *match_filter*. These configuration
    settings can also be passed by argument.

    :arg documents: a sequence of documents.
    :returns: a subset of *documents* that was picked.
    """
    from papis.strings import FormatPattern

    if header_format_file is None and header_format is None:
        header_format_file = papis.config.get("header-format-file")

    if header_format_file is not None:
        if header_format is not None:
            raise ValueError(
                "cannot pass both 'header_format_file' and 'header_format'")

        with open(os.path.expanduser(header_format_file), encoding="utf-8") as fd:
            header_format = FormatPattern(None, fd.read().rstrip())

    if match_format is None:
        match_format = papis.config.getformatpattern("match-format")

    if header_format is None:
        header_format = papis.config.getformatpattern("header-format")

    from functools import partial

    header_filter = partial(papis.format.format, header_format)
    match_filter = partial(papis.format.format, match_format)

    return pick(documents,
                header_filter=header_filter,
                match_filter=match_filter)


def pick_subfolder_from_lib(libname: str) -> list[str]:
    """Pick subfolders from all existing subfolders in *lib*.

    Note that this includes document folders in *lib* as well nested library
    folders.

    :arg libname: the name of an existing library to search in.
    :returns: a subset of the subfolders in the library.
    """
    from papis.api import get_all_documents_in_lib
    documents = get_all_documents_in_lib(libname)

    # get all document directories
    folders = [os.path.dirname(str(d.get_main_folder())) for d in documents]
    # get all library directories
    folders.extend(papis.config.get_lib_from_name(libname).paths)
    # remove duplicates and sort paths
    folders = sorted(set(folders))

    return pick(folders)


def pick_library(libs: list[str] | None = None, *,
                 header_format: "papis.strings.AnyString | None" = None,
                 ) -> list[str]:
    """Pick a library from the current configuration.

    :arg libs: a list of libraries to pick from.
    """
    if libs is None:
        libs = papis.api.get_libraries()

    if header_format is None:
        header_format = papis.config.getformatpattern("library-header-format")

    def header_filter(lib: str) -> str:
        import colorama

        library = papis.config.get_lib_from_name(lib)
        return papis.format.format(header_format, {
            "name": library.name,
            "dir": library.paths[0],
            "paths": library.paths
            }, doc_key="library", additional={"c": colorama})

    return pick(libs,
                header_filter=header_filter,
                match_filter=str)
