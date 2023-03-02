import os
import sys
import re
import pathlib
from itertools import count, product
from typing import (Optional, List, Iterator, Iterable, Any, Dict,
                    Union, Callable, TypeVar, Tuple, TYPE_CHECKING)

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

A = TypeVar("A")
B = TypeVar("B")


def get_session() -> "requests.Session":
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
           xs: List[A],
           np: Optional[int] = None) -> List[B]:
    """
    todo: enable multiprocessing support for darwin (py3.6+) ...
    todo: ... see https://github.com/papis/papis/issues/323
    """
    # FIXME: load singleton plugins here instead of on all the processes
    _ = papis.format.get_formater()

    if np is None:
        np = int(os.environ.get("PAPIS_NP", str(os.cpu_count())))

    if np and HAS_MULTIPROCESSING and sys.platform != "darwin":
        with Pool(np) as pool:
            return list(pool.map(f, xs))
    else:
        return list(map(f, xs))


def general_open(file_name: str,
                 key: str,
                 default_opener: Optional[str] = None,
                 wait: bool = True) -> None:
    """Wrapper for openers
    """
    try:
        opener = papis.config.get(key)
    except papis.exceptions.DefaultSettingValueMissing:
        if default_opener is None:
            default_opener = papis.defaults.get_default_opener()
        opener = default_opener

    import shlex
    cmd = shlex.split("{0} '{1}'".format(opener, file_name))
    logger.debug("cmd: %s", cmd)

    # NOTE: Detached processes do not fail properly when the command does not
    # exist, so we check for it manually here
    import shutil
    if not shutil.which(cmd[0]):
        raise FileNotFoundError(
            "[Errno 2] No such file or directory: '{}'".format(opener))

    import subprocess
    if wait:
        logger.debug("Waiting for process to finish")
        subprocess.call(cmd)
    else:
        logger.debug("Not waiting for process to finish")
        popen_kwargs = {
            "shell": False,
            "stdin": None,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True
        }  # type: Dict[str, Any]

        # NOTE: Detach process so that the terminal can be closed without also
        # closing the 'opentool' itself with the open document
        if sys.platform == "win32":
            popen_kwargs["creationflags"] = subprocess.DETACHED_PROCESS
            popen_kwargs["creationflags"] |= subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            cmd.insert(0, "nohup")

        subprocess.Popen(cmd, **popen_kwargs)


def open_file(file_path: str, wait: bool = True) -> None:
    """Open file using the ``opentool`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :param wait: Wait for the completion of the opener program to continue
    """
    general_open(file_name=file_path, key="opentool", wait=wait)


def get_folders(folder: str) -> List[str]:
    """This is the main indexing routine. It looks inside ``folder`` and crawls
    the whole directory structure in search for subfolders containing an info
    file.

    :param folder: Folder to look into.
    :returns: List of folders containing an info file.
    """
    logger.debug("Indexing folders in '%s'", folder)

    folders = []
    for root, _, _ in os.walk(folder):
        if os.path.exists(
                os.path.join(root, papis.config.getstring("info-name"))):
            folders.append(root)

    logger.debug("%d valid folders retrieved", len(folders))

    return folders


def create_identifier(input_list: str) -> Iterator[str]:
    """This creates a generator object capable of iterating over lists to
    create combinations of that list that result in unique strings.
    Ideally for use in modifying an existing string to make it unique.

    Example:
    >>> import string
    >>> m = create_identifier(string.ascii_lowercase)
    >>> next(m)
    'a'

    (`see here <https://stackoverflow.com/questions/14381940/>`__)

    :param input_list: list to iterate over
    """
    for n in count(1):
        for s in product(input_list, repeat=n):
            yield "".join(s)


def clean_document_name(doc_path: str) -> str:
    """Get a file path and return the basename of the path cleaned.

    It will also turn chinese, french, russian etc into ascii characters.

    :param doc_path: Path of a document.
    :returns: Basename of the path cleaned
    """
    import slugify
    regex_pattern = r"[^a-z0-9.]+"
    return str(slugify.slugify(
        os.path.basename(doc_path),
        word_boundary=True,
        regex_pattern=regex_pattern))


def locate_document_in_lib(document: papis.document.Document,
                           library: Optional[str] = None
                           ) -> papis.document.Document:
    """Try to figure out if a document is already in a library

    :param document: Document to be searched for
    :param library: Name of a valid papis library
    :returns: Document in library if found
    :raises IndexError: Whenever document is not found in the library
    """
    db = papis.database.get(library_name=library)
    comparing_keys = papis.config.getlist("unique-document-keys")
    assert comparing_keys is not None

    for k in comparing_keys:
        if not document.has(k):
            continue
        docs = db.query_dict({k: document[k]})
        if docs:
            return docs[0]

    raise IndexError("Document not found in library")


def locate_document(
        document: papis.document.Document,
        documents: List[papis.document.Document]
        ) -> Optional[papis.document.Document]:
    """Try to figure out if a document is already within a list of documents.

    :param document: Document to be searched for
    :param documents: Documents to search in
    :returns: papis document if it is found
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


def folders_to_documents(folders: List[str]) -> List[papis.document.Document]:
    """Turn folders into documents, this step is quite critical for performance

    :param folders: List of folder paths.
    :returns: List of document objects.
    """
    import time
    begin_t = time.time()
    result = parmap(papis.document.from_folder, folders)

    logger.debug("Done in %.1f ms", 1000 * (time.time() - begin_t))
    return result


def get_cache_home() -> str:
    """Get folder where the cache files are stored, it retrieves the
    ``cache-dir`` configuration setting. It is ``XDG`` standard compatible.

    :returns: Full path for cache main folder
    """
    user_defined = papis.config.get("cache-dir")
    if user_defined is not None:
        path = os.path.expanduser(user_defined)
    else:
        path = os.path.expanduser(
            os.path.join(str(os.environ.get("XDG_CACHE_HOME")), "papis")
        ) if os.environ.get(
            "XDG_CACHE_HOME"
        ) else os.path.expanduser(
            os.path.join("~", ".cache", "papis")
        )
    if not os.path.exists(path):
        os.makedirs(path)
    return str(path)


def get_matching_importer_or_downloader(
        uri: str,
        only_data: bool = True,
        ) -> List[papis.importer.Importer]:
    """Gets all the importers and downloaders that match *uri*.

    This function tries to match the URI using :meth:`~papis.importer.Importer.match`
    and extract the data using :meth:`~papis.importer.Importer.fetch`. Only
    importers that fetch the data without issues are returned.

    :param uri: an URI to match the importers against.
    :param only_data: if *True*, attempt to only import document data, not files.
    """
    result = []

    all_importer_classes = (
        papis.importer.get_importers()
        + papis.downloaders.get_available_downloaders())

    for cls in all_importer_classes:
        name = "{}.{}".format(cls.__module__, cls.__name__)
        logger.debug("Trying with importer "
                     "{c.Back.BLACK}{c.Fore.YELLOW}%s{c.Style.RESET_ALL}",
                     name)

        try:
            importer = cls.match(uri)
        except Exception:
            logger.debug("%s failed to match query: '%s'.", name, uri)
            importer = None

        if importer:
            try:
                if only_data:
                    # NOTE: not all importers can (or do) separate the fetching
                    # of data and files, so we try both cases for now
                    try:
                        importer.fetch_data()
                    except NotImplementedError:
                        importer.fetch()
                else:
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
        only_data: bool = True,
        ) -> List[papis.importer.Importer]:
    """Get importers that match the given URIs.
    This function tries to match the URI using :meth:`~papis.importer.Importer.match`
    and extract the data using :meth:`~papis.importer.Importer.fetch`. Only
    importers that fetch the data without issues are returned.
    :param name_and_uris: an list of ``(name, uri)`` of importer names and
        URIs to match them against.
    :param only_data: if *True*, attempt to only import document data, not files.
    """
    import_mgr = papis.importer.get_import_mgr()

    result = []
    for name, uri in name_and_uris:
        try:
            importer = import_mgr[name].plugin(uri=uri)
            if only_data:
                # NOTE: not all importers can (or do) separate the fetching
                # of data and files, so we try both cases for now
                try:
                    importer.fetch_data()
                except NotImplementedError:
                    importer.fetch()
            else:
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
        only_data: bool = True,
        ) -> papis.importer.Context:
    """Collect all data from the given *importers*.
    It is assumed that the importers have called the needed ``fetch`` methods,
    so all data has been downloaded and converted. This function is meant to
    only do the aggregation.
    :param batch: if *True*, overwrite data from previous importers, otherwise
        ask the user to manually merge.
    :param only_data: if *True*, only import document data, not files.
    """
    ctx = papis.importer.Context()
    if not importers:
        return ctx

    for importer in importers:
        if importer.ctx.data:
            logger.info("Merging data from importer '%s'.", importer.name)
            if batch:
                ctx.data.update(importer.ctx.data)
            else:
                papis.utils.update_doc_from_data_interactively(
                    ctx.data,
                    importer.ctx.data,
                    str(importer))

        if not only_data and importer.ctx.files:
            logger.info("Got files from importer '%s':\n\t%s",
                        importer.name,
                        "\n\t".join(importer.ctx.files))

            msg = "Use this file? (from {})".format(importer.name)
            for f in importer.ctx.files:
                papis.utils.open_file(f)
                if batch or papis.tui.utils.confirm(msg):
                    ctx.files.append(f)

    return ctx


def update_doc_from_data_interactively(
        document: Union[papis.document.Document, Dict[str, Any]],
        data: Dict[str, Any], data_name: str) -> None:
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


def is_relative_to(path: str, other: str) -> bool:
    if sys.version_info >= (3, 9):
        return pathlib.Path(path).is_relative_to(other)
    # This should lead to the same result as the above for older versions of
    # python.
    else:
        try:
            return not os.path.relpath(path, start=other).startswith("..")
        except ValueError:
            return False


def dump_object_doc(
        objects: Iterable[Tuple[str, Any]],
        sep: str = "\n\t") -> List[str]:
    import colorama
    re_whitespace = re.compile(r"\s+")

    result = []
    for name, obj in objects:
        if obj.__doc__:
            lines = [line for line in obj.__doc__.split("\n\n") if line]
        else:
            lines = ["No description."]

        headline = re_whitespace.sub(" ", lines[0].strip())
        result.append("{c.Style.BRIGHT}{name}{c.Style.RESET_ALL}{sep}{headline}"
                      .format(c=colorama, name=name, sep=sep, headline=headline))

    return result
