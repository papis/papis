import os
import sys
import re
import logging
from itertools import count, product
from typing import (Optional, List, Iterator, Any, Dict,
                    Union, Callable, TypeVar)

try:
    import multiprocessing.synchronize  # noqa: F401
    from multiprocessing import Pool
    HAS_MULTIPROCESSING = True
except ImportError:
    HAS_MULTIPROCESSING = False

import papis.config
import papis.exceptions
import papis.importer
import papis.downloaders
import papis.document
import papis.database

logger = logging.getLogger("utils")

A = TypeVar("A")
B = TypeVar("B")


def has_multiprocessing() -> bool:
    return HAS_MULTIPROCESSING


def parmap(f: Callable[[A], B],
           xs: List[A],
           np: Optional[int] = None) -> List[B]:
    if has_multiprocessing() and sys.platform != 'darwin':
        np = np or os.cpu_count()
        np = int(os.environ.get("PAPIS_NP", str(np)))
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
            default_opener = papis.config.get_default_opener()
        opener = default_opener

    import shlex
    cmd = shlex.split("{0} '{1}'".format(opener, file_name))
    logger.debug("cmd: %s", cmd)

    import subprocess
    if wait:
        logger.debug("Waiting for process to finish")
        subprocess.call(cmd)
    else:
        logger.debug("Not waiting for process to finish")
        subprocess.Popen(
            cmd, shell=False,
            stdin=None, stdout=None, stderr=None, close_fds=True)


def open_file(file_path: str, wait: bool = True) -> None:
    """Open file using the ``opentool`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :type  file_path: str
    :param wait: Wait for the completion of the opener program to continue
    :type  wait: bool

    """
    general_open(file_name=file_path, key="opentool", wait=wait)


def get_folders(folder: str) -> List[str]:
    """This is the main indexing routine. It looks inside ``folder`` and crawls
    the whole directory structure in search for subfolders containing an info
    file.

    :param folder: Folder to look into.
    :type  folder: str
    :returns: List of folders containing an info file.
    :rtype: list
    """
    logger.debug("Indexing folders in '%s'", folder)

    folders = []
    for root, dirnames, filenames in os.walk(folder):
        if os.path.exists(
                os.path.join(root, papis.config.getstring('info-name'))):
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

    (`see <
        https://stackoverflow.com/questions/14381940/
        >`_)

    :param input_list: list to iterate over
    :type  input_list: list

    """
    for n in count(1):
        for s in product(input_list, repeat=n):
            yield ''.join(s)


def clean_document_name(doc_path: str) -> str:
    """Get a file path and return the basename of the path cleaned.

    It will also turn chinese, french, russian etc into ascii characters.

    :param doc_path: Path of a document.
    :type  doc_path: str
    :returns: Basename of the path cleaned
    :rtype:  str

    """
    import slugify
    regex_pattern = r'[^a-z0-9.]+'
    return str(slugify.slugify(
        os.path.basename(doc_path),
        word_boundary=True,
        regex_pattern=regex_pattern))


def locate_document_in_lib(document: papis.document.Document,
                           library: Optional[str] = None
                           ) -> papis.document.Document:
    """Try to figure out if a document is already in a library

    :param document: Document to be searched for
    :type  document: papis.document.Document
    :param library: Name of a valid papis library
    :type  library: str
    :returns: Document in library if found
    :rtype:  papis.document.Document
    :raises IndexError: Whenever document is not found in the library
    """
    db = papis.database.get(library_name=library)
    comparing_keys = papis.config.getlist('unique-document-keys')
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
    :type  document: papis.document.Document
    :param documents: Documents to search in
    :type  documents: list
    :returns: papis document if it is found

    """
    # if these keys exist in the documents, then check those first
    # TODO: find a way to really match well titles and author
    comparing_keys = papis.config.getlist('unique-document-keys')
    assert comparing_keys is not None
    for d in documents:
        for key in comparing_keys:
            if key in document.keys() and key in d.keys():
                if re.match(document[key], d[key], re.I):
                    return d
    return None


def folders_to_documents(folders: List[str]) -> List[papis.document.Document]:
    """Turn folders into documents, this step is quite critical for performance

    :param folders: List of folder paths.
    :type  folders: list
    :returns: List of document objects.
    :rtype:  list

    """
    logger = logging.getLogger("utils:folders_to_documents")

    import time
    begin_t = time.time()
    result = parmap(papis.document.from_folder, folders)

    logger.debug("Done in %.1f ms", 1000*(time.time() - begin_t))
    return result


def get_cache_home() -> str:
    """Get folder where the cache files are stored, it retrieves the
    ``cache-dir`` configuration setting. It is ``XDG`` standard compatible.

    :returns: Full path for cache main folder
    :rtype:  str

    """
    user_defined = papis.config.get('cache-dir')
    if user_defined is not None:
        path = os.path.expanduser(user_defined)
    else:
        path = os.path.expanduser(
            os.path.join(str(os.environ.get('XDG_CACHE_HOME')), 'papis')
        ) if os.environ.get(
            'XDG_CACHE_HOME'
        ) else os.path.expanduser(
            os.path.join('~', '.cache', 'papis')
        )
    if not os.path.exists(path):
        os.makedirs(path)
    return str(path)


def get_matching_importer_or_downloader(matching_string: str
                                        ) -> List[papis.importer.Importer]:
    logger = logging.getLogger("utils:matcher")

    importers = []  # type: List[papis.importer.Importer]
    _imps = papis.importer.get_importers()
    _downs = papis.downloaders.get_available_downloaders()
    _all_importers = list(_imps) + list(_downs)
    for importer_cls in _all_importers:
        logger.debug("trying with importer "
                     "{c.Back.BLACK}{c.Fore.YELLOW}%s{c.Style.RESET_ALL}",
                     importer_cls)
        try:
            importer = importer_cls.match(
                matching_string)  # type: Optional[papis.importer.Importer]
        except Exception as e:
            logger.error(e)
            continue
        if importer:
            logger.info(
                    "%s {c.Back.BLACK}{c.Fore.GREEN}"
                    "matches %s{c.Style.RESET_ALL}",
                    matching_string, importer.name)
            try:
                importer.fetch()
            except Exception as e:
                logger.error(e)
            else:
                importers.append(importer)
    return importers


def update_doc_from_data_interactively(
        document: Union[papis.document.Document, Dict[str, Any]],
        data: Dict[str, Any], data_name: str) -> None:
    import copy
    docdata = copy.copy(document)

    import papis.tui.widgets.diff
    # do not compare some entries
    docdata.pop('files', None)
    docdata.pop('tags', None)
    document.update(papis.tui.widgets.diff.diffdict(
                        docdata,
                        data,
                        namea=papis.document.describe(document),
                        nameb=data_name))
