import os
import sys
import re
import pathlib
from typing import (Optional, List, Iterator, Iterable, Any, Dict,
                    Union, Callable, Sequence, TypeVar, Tuple, TYPE_CHECKING)

try:
    import multiprocessing.synchronize  # noqa: F401
    from multiprocessing import Pool
    HAS_MULTIPROCESSING = True
except ImportError:
    HAS_MULTIPROCESSING = False

import papis.config
import papis.format
import papis.exceptions
import papis.importer
import papis.downloaders
import papis.document
import papis.database
import papis.defaults
import papis.logging

logger = papis.logging.get_logger(__name__)

if TYPE_CHECKING:
    import requests

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
           np: Optional[int] = None) -> List[B]:
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

    # FIXME: load singleton plugins here instead of on all the processes
    _ = papis.format.get_formatter()

    if np is None:
        np = int(os.environ.get("PAPIS_NP", str(os.cpu_count())))

    if np and HAS_MULTIPROCESSING and sys.platform != "darwin":
        with Pool(np) as pool:
            return list(pool.map(f, xs))
    else:
        return list(map(f, xs))


def run(cmd: Sequence[str],
        wait: bool = True,
        env: Optional[Dict[str, Any]] = None,
        cwd: Optional[str] = None) -> None:
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
        platform_kwargs: Dict[str, Any] = {}
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
                 default_opener: Optional[str] = None,
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

    try:
        opener = papis.config.get(key)
    except papis.exceptions.DefaultSettingValueMissing:
        if default_opener is None:
            default_opener = papis.defaults.get_default_opener()

        opener = default_opener

    import shlex

    # NOTE: 'opener' can be a command with arguments, so we split it properly
    is_windows = sys.platform == "win32"
    cmd = shlex.split(str(opener), posix=not is_windows) + [file_name]

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


def get_folders(folder: str) -> List[str]:
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


def create_identifier(input_list: Optional[str] = None, skip: int = 0) -> Iterator[str]:
    """Creates an infinite list of identifiers based on *input_list*.

    This creates a generator object capable of iterating over lists to
    create unique products of increasing cardinality
    (see `here <https://stackoverflow.com/questions/14381940/python-pair-alphabets-after-loop-is-completed>`__).
    This is mainly intended to create suffixes for existing strings, e.g. file names,
    to ensure uniqueness.

    :param input_list: list to iterate over
    :param skip: number of identifiers to skip (negative integers are set to 0).

    >>> import string
    >>> m = create_identifier(string.ascii_lowercase)
    >>> next(m)
    'a'
    """  # noqa: E501
    import string
    from itertools import count, product, islice

    def ids() -> Iterator[str]:
        inputs = string.ascii_lowercase if input_list is None else input_list

        for n in count(1):
            for s in product(inputs, repeat=n):
                yield "".join(s)

    yield from islice(ids(), max(skip, 0), None)


def clean_document_name(doc_path: str, is_path: bool = True) -> str:
    """Clean a string to only contain visible ASCII characters.

    This function uses `slugify <https://github.com/un33k/python-slugify>`__ to
    create ASCII strings that can be used safely as file names or printed to
    consoles that do not necessarily support full unicode.

    By default, it assumes that the input is a path and will only look at its
    ``basename``. This can have unintended results for other strings and can
    be disabled by setting *is_path* to *False*.

    :param doc_path: a string to be cleaned.
    :param is_path: if *True*, only the basename of *doc_path* is cleaned, as
        obtained from :func:`os.path.basename`.
    :returns: a cleaned ASCII string.
    """
    if is_path:
        doc_path = os.path.basename(doc_path)

    import slugify
    regex_pattern = r"[^a-z0-9.]+"
    return str(slugify.slugify(
        doc_path,
        word_boundary=True,
        regex_pattern=regex_pattern))


def locate_document_in_lib(document: papis.document.Document,
                           library: Optional[str] = None) -> papis.document.Document:
    """Locate a document in a library.

    This function uses the :confval:`unique-document-keys`
    to determine if the current document matches any document in the library.
    The first document for which a key matches exactly will be returned.

    :param document: the document to search for.
    :param library: the name of a valid ``papis`` library.
    :returns: a full document as found in the library.

    :raises IndexError: No document found in the library.
    """

    db = papis.database.get(library_name=library)

    comparing_keys = papis.config.getlist("unique-document-keys")
    assert comparing_keys is not None

    for key in comparing_keys:
        value = document.get(key)
        if value is None:
            continue

        docs = db.query_dict({key: value})
        if docs:
            return docs[0]

    raise IndexError("Document not found in library: '{}'"
                     .format(papis.document.describe(document)))


def locate_document(
        document: papis.document.Document,
        documents: Iterable[papis.document.Document]
        ) -> Optional[papis.document.Document]:
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


def folders_to_documents(folders: Iterable[str]) -> List[papis.document.Document]:
    """Load a list of documents from their respective *folders*.

    :param folders: a list of folder paths to load from.
    :returns: a list of document objects.
    """

    import time
    begin_t = time.time()
    result = parmap(papis.document.from_folder, folders)

    logger.debug("Finished in %.1f ms.", 1000 * (time.time() - begin_t))
    return result


def update_doc_from_data_interactively(
        document: Union[papis.document.Document, Dict[str, Any]],
        data: Dict[str, Any],
        data_name: str) -> None:
    """Shows a TUI to update the *document* interactively with fields from *data*.

    :param document: a document (or a mapping convertible to a document) which
        is going to be updated.
    :param data: additional data to select and merge into *document*.
    :param data_name: an identifier for the *data* to show in the TUI.
    """
    import copy
    docdata = copy.copy(document)

    import papis.tui.widgets.diff
    # do not compare some entries
    docdata.pop("files", None)
    docdata.pop("tags", None)

    document.update(papis.tui.widgets.diff.diffdict(
                    docdata,
                    data,
                    namea=papis.document.describe(document),
                    nameb=data_name))


def get_cache_home() -> str:
    """Get default cache directory.

    This will retrieve the :confval:`cache-dir` configuration setting.
    It is ``XDG`` standard compatible.

    :returns: the absolute path for the cache main folder.
    """
    cachedir = papis.config.get("cache-dir")

    if cachedir is None:
        xdg_cache_dir = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache_dir:
            cachedir = os.path.join(xdg_cache_dir, "papis")
        else:
            cachedir = os.path.join("~", ".cache", "papis")

    # ensure the directory exists
    cachedir = os.path.expanduser(cachedir)
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)

    return cachedir


def get_matching_importer_or_downloader(
        uri: str,
        download_files: Optional[bool] = None,
        only_data: Optional[bool] = None
        ) -> List[papis.importer.Importer]:
    """Gets all the importers and downloaders that match *uri*.

    This function tries to match the URI using :meth:`~papis.importer.Importer.match`
    and extract the data using :meth:`~papis.importer.Importer.fetch`. Only
    importers that fetch the data without issues are returned.

    :param uri: an URI to match the importers against.
    :param download_files: if *True*, importers and downloaders also try to
        download files (PDFs, etc.) instead of just metadata.
    """
    # FIXME: this is here for backwards compatibility and should be removed
    # before we release the next version
    if only_data is not None and download_files is not None:
        raise ValueError("Cannot pass both 'only_data' and 'download_files'")

    if only_data is not None:
        download_files = not only_data

    if download_files is None:
        download_files = False

    result = []

    all_importer_classes = (
        papis.importer.get_importers()
        + papis.downloaders.get_available_downloaders())

    for cls in all_importer_classes:
        name = f"{cls.__module__}.{cls.__name__}"
        logger.debug("Trying with importer "
                     "{c.Back.BLACK}{c.Fore.YELLOW}%s{c.Style.RESET_ALL}.",
                     name)

        try:
            importer = cls.match(uri)
        except Exception:
            logger.debug("%s failed to match query: '%s'.", name, uri)
            importer = None

        if importer:
            try:
                if download_files:
                    importer.fetch()
                else:
                    # NOTE: not all importers can (or do) separate the fetching
                    # of data and files, so we try both cases for now
                    try:
                        importer.fetch_data()
                    except NotImplementedError:
                        importer.fetch()
            except Exception:
                logger.debug("%s (%s) failed to fetch query: '%s'.",
                             name, importer.name, uri)
            else:
                logger.info(
                    "{c.Back.BLACK}{c.Fore.GREEN}%s (%s) fetched data for query '%s'!"
                    "{c.Style.RESET_ALL}",
                    name, importer.name, uri)

                result.append(importer)

    return result


def get_matching_importer_by_name(
        name_and_uris: Iterable[Tuple[str, str]],
        download_files: Optional[bool] = None,
        only_data: Optional[bool] = None,
        ) -> List[papis.importer.Importer]:
    """Get importers that match the given URIs.

    This function tries to match the URI using :meth:`~papis.importer.Importer.match`
    and extract the data using :meth:`~papis.importer.Importer.fetch`. Only
    importers that fetch the data without issues are returned.

    :param name_and_uris: an list of ``(name, uri)`` of importer names and
        URIs to match them against.
    :param download_files: if *True*, importers and downloaders also try to
        download files (PDFs, etc.) instead of just metadata.
    """
    # FIXME: this is here for backwards compatibility and should be removed
    # before we release the next version
    if only_data is not None and download_files is not None:
        raise ValueError("Cannot pass both 'only_data' and 'download_files'")

    if only_data is not None:
        download_files = not only_data

    if download_files is None:
        download_files = False

    import_mgr = papis.importer.get_import_mgr()

    result = []
    for name, uri in name_and_uris:
        try:
            importer = import_mgr[name].plugin(uri=uri)
            if download_files:
                importer.fetch()
            else:
                # NOTE: not all importers can (or do) separate the fetching
                # of data and files, so we try both cases for now
                try:
                    importer.fetch_data()
                except NotImplementedError:
                    importer.fetch()

            if importer.ctx:
                result.append(importer)
        except Exception as exc:
            logger.debug("Failed to match importer '%s': '%s'.",
                         name, uri, exc_info=exc)

    return result


def collect_importer_data(
        importers: Iterable[papis.importer.Importer],
        batch: bool = True,
        use_files: Optional[bool] = None,
        only_data: Optional[bool] = None,
        ) -> papis.importer.Context:
    """Collect all data from the given *importers*.

    It is assumed that the importers have called the needed ``fetch`` methods,
    so all data has been downloaded and converted. This function is meant to
    only do the aggregation.

    :param batch: if *True*, overwrite data from previous importers, otherwise
        ask the user to manually merge.
    :param use_files: if *True*, both metadata and files are collected
        from the importers.
    """
    # FIXME: this is here for backwards compatibility and should be removed
    # before we release the next version
    if only_data is not None and use_files is not None:
        raise ValueError("Cannot pass both 'only_data' and 'use_files'")

    if only_data is not None:
        use_files = not only_data

    if use_files is None:
        use_files = False

    ctx = papis.importer.Context()
    if not importers:
        return ctx

    for importer in importers:
        if importer.ctx.data:
            logger.info("Merging data from importer '%s'.", importer.name)
            if batch:
                ctx.data.update(importer.ctx.data)
            else:
                if ctx.data:
                    update_doc_from_data_interactively(
                        ctx.data,
                        importer.ctx.data,
                        str(importer))
                else:
                    # NOTE: first importer does not require interactive use
                    ctx.data.update(importer.ctx.data)

        if use_files and importer.ctx.files:
            logger.info("Got files from importer '%s':\n\t%s",
                        importer.name,
                        "\n\t".join(importer.ctx.files))

            msg = f"Use this file? (from {importer.name})"
            for f in importer.ctx.files:
                open_file(f)
                if batch or papis.tui.utils.confirm(msg):
                    ctx.files.append(f)

    return ctx


def is_relative_to(path: str, other: str) -> bool:
    """Check if paths are relative to each other.

    This is equivalent to :meth:`pathlib.PurePath.is_relative_to`.

    :returns: *True* if *path* is relative to the *other* path.
    """
    if sys.version_info >= (3, 9):
        return pathlib.Path(path).is_relative_to(other)
    # This should lead to the same result as the above for older versions of
    # python.
    else:
        try:
            return not os.path.relpath(path, start=other).startswith("..")
        except ValueError:
            return False
