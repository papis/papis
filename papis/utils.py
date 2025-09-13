import os
import re
import sys
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import TYPE_CHECKING, Any, TypeVar
from warnings import warn

try:
    # NOTE: multiprocessing is not available on some platforms (e.g. Android)
    import multiprocessing.synchronize  # noqa: F401
    from multiprocessing import Pool
    HAS_MULTIPROCESSING = True
except ImportError:
    HAS_MULTIPROCESSING = False

import platformdirs

import papis.config
import papis.logging

logger = papis.logging.get_logger(__name__)

if TYPE_CHECKING:
    import requests

    import papis.document
    import papis.importer

#: Invariant :class:`typing.TypeVar`
A = TypeVar("A")
#: Invariant :class:`typing.TypeVar`
B = TypeVar("B")


def get_session() -> "requests.Session":
    """Create a :class:`requests.Session` for ``papis``.

    This session has the expected ``User-Agent`` (see
    :confval:`user-agent`), proxy (see
    :confval:`downloader-proxy`) and other settings used
    for ``papis``. It is recommended to use it instead of creating a
    :class:`requests.Session` at every call site.
    """
    import requests
    session = requests.Session()
    session.headers.update({
        "User-Agent": papis.config.getstring("user-agent"),
    })

    proxy = papis.config.get("downloader-proxy")
    if proxy is not None:
        session.proxies = {
            "http": proxy,
            "https": proxy,
        }

    return session


def has_multiprocessing() -> bool:
    return HAS_MULTIPROCESSING


def parmap(f: Callable[[A], B],
           xs: Iterable[A],
           np: int | None = None) -> list[B]:
    """Apply the function *f* to all elements of *xs*.

    When available, this function uses the :mod:`multiprocessing` module to
    apply the function in parallel. This can have a noticeable performance
    impact when the number of elements of *xs* is large, but can also be slower
    than a sequential :func:`map`.

    The number of processes can also be controlled using the ``PAPIS_NP``
    environment variable. Setting this variable to ``0`` will disable the
    use of :mod:`multiprocessing` on all platforms.

    .. todo::

        Enable multiprocessing support for Darwin on Python 3.6+. For details
        see `this issues <https://github.com/papis/papis/issues/323>`__.

    :param f: a callable to apply to a list of elements.
    :param xs: an iterable of elements to apply the function *f* to.
    :param np: number of processes to use when applying the function *f* in
        parallel. This value defaults to ``PAPIS_NP`` or :func:`os.cpu_count`.
    """
    if np is None:
        np = int(os.environ.get("PAPIS_NP", str(os.cpu_count())))

    if np and HAS_MULTIPROCESSING and sys.platform != "darwin":
        with Pool(np) as pool:
            return list(pool.map(f, xs))
    else:
        return list(map(f, xs))


def run(cmd: Sequence[str],
        wait: bool = True,
        env: dict[str, Any] | None = None,
        cwd: str | None = None) -> None:
    """Run a given command with :mod:`subprocess`.

    This is a simple wrapper around :class:`subprocess.Popen` with custom
    defaults used to call `papis` commands.

    :arg cmd: a sequence of arguments to run, where the first entry is expected
        to be the command name and the remaining entries its arguments.
    :param wait: if *True* wait for the process to finish, otherwise detach the
        process and return immediately.
    :param env: a mapping that defines additional environment variables for
        the child process.
    :param cwd: current working directory in which to run the command.
    """

    cmd = list(cmd)
    if not cmd:
        return

    if cwd:
        cwd = os.path.expanduser(cwd)
        logger.debug("Changing directory to '%s'.", cwd)

    logger.debug("Running command: '%s'.", cmd)

    # NOTE: detached processes do not fail properly when the command does not
    # exist, so we check for it manually here
    import shutil
    if not shutil.which(cmd[0]):
        raise FileNotFoundError(f"Command not found: '{cmd[0]}'")

    import subprocess
    if wait:
        logger.debug("Waiting for process to finish.")
        subprocess.call(cmd, shell=False, cwd=cwd, env=env)
    else:
        # NOTE: detach process so that the terminal can be closed without also
        # closing the 'opentool' itself with the open document
        platform_kwargs: dict[str, Any] = {}
        if sys.platform == "win32":
            platform_kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            # NOTE: 'close_fds' is not supported on windows with stdout/stderr
            # https://docs.python.org/3/library/subprocess.html#subprocess.Popen
            platform_kwargs["close_fds"] = True
            cmd.insert(0, "nohup")

        logger.debug("Not waiting for process to finish.")
        subprocess.Popen(cmd,
                         shell=False,
                         cwd=cwd,
                         env=env,
                         stdin=None,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         **platform_kwargs)


def general_open(file_name: str,
                 key: str,
                 default_opener: str | None = None,
                 wait: bool = True) -> None:
    """Open a file with a configured open tool (executable).

    :param file_name: a file path to open.
    :param key: a key in the configuration file to determine the opener used,
        e.g. :confval:`opentool`.
    :param default_opener: an existing executable that can be used to open the
        file given by *file_name*. By default, the opener given by
        *key*, if any, or the default ``papis`` opener are used.
    :param wait: if *True* wait for the process to finish, otherwise detach the
        process and return immediately.
    """
    from papis.exceptions import DefaultSettingValueMissing

    try:
        opener = papis.config.get(key)
    except DefaultSettingValueMissing:
        if default_opener is None:
            from papis.defaults import get_default_opener
            default_opener = get_default_opener()

        opener = default_opener

    import shlex

    # NOTE: 'opener' can be a command with arguments, so we split it properly
    is_windows = sys.platform == "win32"
    cmd = [*shlex.split(str(opener), posix=not is_windows), file_name]

    import shutil
    if shutil.which(cmd[0]) is None:
        raise FileNotFoundError(
            f"Command not found for '{key}': '{opener}'")

    run(cmd, wait=wait)


def open_file(file_path: str, wait: bool = True) -> None:
    """Open file using the configured :confval:`opentool`.

    :param file_path: a file path to open.
    :param wait: if *True* wait for the process to finish, otherwise detach the
        process and return immediately.
    """
    general_open(file_name=file_path, key="opentool", wait=wait)


def get_folders(folder: str) -> list[str]:
    """Get all folders with ``papis`` documents inside of *folder*.

    This is the main indexing routine. It looks inside *folder* and crawls
    the whole directory structure in search of subfolders containing an ``info``
    file. The name of the file must match the configured
    :confval:`info-name`.

    :param folder: root folder to look into.
    :returns: List of folders containing an ``info`` file.
    """
    logger.debug("Indexing folders in '%s'.", folder)
    info_name = papis.config.getstring("info-name")

    folders = []
    for root, _, _ in os.walk(folder):
        if os.path.exists(os.path.join(root, info_name)):
            folders.append(root)

    logger.debug("Retrieved %d valid folders.", len(folders))

    return folders


def create_identifier(input_list: str | None = None, skip: int = 0) -> Iterator[str]:
    warn("'papis.utils.create_identifier' is deprecated and will be removed in "
         "Papis v0.16. Use 'papis.paths.unique_suffixes' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.paths import unique_suffixes
    yield from unique_suffixes(input_list, skip=skip)


def clean_document_name(doc_path: str, is_path: bool = True) -> str:
    warn("'papis.utils.clean_document_name' is deprecated and will be removed in "
         "Papis v0.16. Use 'papis.paths.normalize_path' instead.",
         DeprecationWarning, stacklevel=2)

    if is_path:
        doc_path = os.path.basename(doc_path)

    from papis.paths import normalize_path
    return normalize_path(doc_path)


def locate_document_in_lib(document: "papis.document.Document",
                           library: str | None = None,
                           *,
                           unique_document_keys: list[str] | None = None,
                           ) -> "papis.document.Document":
    """Locate a document in a library.

    This function falls back to :confval:`unique-document-keys` to determine if the
    current document matches any document in the library. The first document
    for which one of the keys in the list matches exactly will be returned.

    :param library: the name of a valid Papis library.
    :param unique_document_keys: a list of keys to match when locating a document.

    :returns: a full document as found in the library.
    :raises IndexError: No document found in the library.
    """
    if unique_document_keys is None:
        unique_document_keys = papis.config.getlist("unique-document-keys")

    from papis.database import get
    db = get(library_name=library)

    for key in unique_document_keys:
        value = document.get(key)
        if value is None:
            continue

        docs = db.query_dict({key: value})
        if docs:
            return docs[0]

    from papis.document import describe
    raise IndexError(f"Document not found in library: '{describe(document)}'")


def locate_document(
        document: "papis.document.Document",
        documents: Iterable["papis.document.Document"]
        ) -> "papis.document.Document | None":
    """Locate a *document* in a list of *documents*.

    This function uses the :confval:`unique-document-keys`
    to determine if the current document matches any document in the list.
    The first document for which a key matches exactly will be returned.

    :param document: the document to search for.
    :param documents: an iterable of existing documents to match against.
    :returns: a document from *documents* which matches the given *document*
        or *None* if no document is found.
    """

    # if these keys exist in the documents, then check those first
    # TODO: find a way to really match well titles and author
    comparing_keys = papis.config.getlist("unique-document-keys")
    assert comparing_keys is not None

    for d in documents:
        for key in comparing_keys:
            if key in document and key in d:
                if re.match(document[key], d[key], re.I):
                    return d

    return None


def folders_to_documents(folders: Iterable[str]) -> list["papis.document.Document"]:
    """Load a list of documents from their respective *folders*.

    :param folders: a list of folder paths to load from.
    :returns: a list of document objects.
    """

    import time

    from papis.document import from_folder

    begin_t = time.time()
    result = parmap(from_folder, folders)

    logger.debug("Finished in %.1f ms.", 1000 * (time.time() - begin_t))
    return result


def update_doc_from_data_interactively(
        document: "papis.document.DocumentLike",
        data: dict[str, Any],
        data_name: str) -> None:
    """Shows a TUI to update the *document* interactively with fields from *data*.

    :param document: a document (or a mapping convertible to a document) which
        is going to be updated.
    :param data: additional data to select and merge into *document*.
    :param data_name: an identifier for the *data* to show in the TUI.
    """
    import copy
    docdata = copy.copy(document)

    from papis.document import describe
    from papis.tui.diff import diffdict

    # do not compare some entries
    docdata.pop("files", None)
    docdata.pop("tags", None)

    diff = diffdict(docdata,
                    data,
                    namea=describe(document),
                    nameb=data_name)
    document.update(diff)


def get_cache_home() -> str:
    """Get default cache directory.

    This will retrieve the :confval:`cache-dir` configuration setting.
    If not provided, a platform-dependent cache folder is chosen instead.

    :returns: the absolute path for the cache main folder.
    """
    cachedir = papis.config.get("cache-dir")
    if cachedir is None:
        cachedir = os.environ.get("PAPIS_CACHE_DIR")
        if cachedir is None:
            cachedir = platformdirs.user_cache_dir("papis")

    if not os.path.exists(cachedir):
        os.makedirs(cachedir)

    return cachedir


def get_matching_importer_or_downloader(
        uri: str,
        download_files: bool | None = None,
        only_data: bool | None = None
        ) -> list["papis.importer.Importer"]:
    # FIXME: this is here for backwards compatibility and should be removed
    # before we release the next version
    if only_data is not None and download_files is not None:
        raise ValueError("Cannot pass both 'only_data' and 'download_files'")

    if only_data is not None:
        download_files = not only_data

    if download_files is None:
        download_files = False

    warn("'papis.utils.get_matching_importer_or_downloader' is deprecated "
         "and will be removed in Papis v0.16. "
         "Use 'papis.importer.get_matching_importers_by_uri' and "
         "'papis.importer.fetch_importers' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.importer import fetch_importers, get_matching_importers_by_uri

    matching_importers = get_matching_importers_by_uri(uri, include_downloaders=True)
    return fetch_importers(matching_importers, download_files=download_files)


def get_matching_importer_by_name(
        name_and_uris: Iterable[tuple[str, str]],
        download_files: bool | None = None,
        only_data: bool | None = None,
        ) -> list["papis.importer.Importer"]:
    # FIXME: this is here for backwards compatibility and should be removed
    # before we release the next version
    if only_data is not None and download_files is not None:
        raise ValueError("Cannot pass both 'only_data' and 'download_files'")

    if only_data is not None:
        download_files = not only_data

    if download_files is None:
        download_files = False

    warn("'papis.utils.get_matching_importer_by_name' is deprecated "
         "and will be removed in Papis v0.16. "
         "Use 'papis.importer.get_matching_importers_by_name' and "
         "'papis.importer.fetch_importers' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.importer import fetch_importers, get_matching_importers_by_name

    matching_importers = get_matching_importers_by_name(name_and_uris)
    return fetch_importers(matching_importers, download_files=download_files)


def collect_importer_data(
        importers: Iterable["papis.importer.Importer"],
        batch: bool = True,
        use_files: bool | None = None,
        only_data: bool | None = None,
        ) -> "papis.importer.Context":
    # FIXME: this is here for backwards compatibility and should be removed
    # before we release the next version
    if only_data is not None and use_files is not None:
        raise ValueError("Cannot pass both 'only_data' and 'use_files'")

    if only_data is not None:
        use_files = not only_data

    if use_files is None:
        use_files = False

    warn("'papis.utils.collect_importer_data' is deprecated "
         "and will be removed in Papis v0.16. "
         "Use 'papis.importer.collect_from_importers' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.importer import collect_from_importers
    return collect_from_importers(importers, batch=batch, use_files=use_files)


def is_relative_to(path: str, other: str) -> bool:
    warn("'papis.utils.is_relative_to' is deprecated and will be removed in "
         "Papis v0.16. Use 'papis.paths.is_relative_to' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.paths import is_relative_to as _is_relative_to
    return _is_relative_to(path, other)


def symlink(source: str, destination: str) -> None:
    warn("'papis.utils.symlink' is deprecated and will be removed in "
         "Papis v0.16. Use 'papis.paths.symlink' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.paths import symlink as _symlink
    return _symlink(source, destination)
