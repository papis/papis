import os
import sys
from itertools import chain
from typing import Dict, List, Match, Optional, Pattern, Tuple

import papis.utils
import papis.docmatcher
import papis.document
import papis.config
import papis.format
import papis.database.base
import papis.logging
from papis.strings import AnyString

logger = papis.logging.get_logger(__name__)


def get_cache_file_name(libpaths: str) -> str:
    """Create a cache file name out of the path of a given directory.

    :param libpaths: folder names to be used as a seed for the cache name.
    :returns: a name for the cache file specific to *libpaths*.

    >>> get_cache_file_name('path/to/my/lib')
    'a8c689820a94babec20c5d6269c7d488-lib'
    >>> get_cache_file_name('papers')
    'a566b2bebc62611dff4cdaceac1a7bbd-papers'
    """
    import hashlib

    hash = hashlib.md5(libpaths.encode()).hexdigest()
    basename = os.path.basename(libpaths)
    return f"{hash}-{basename}"


def get_cache_file_path(libpaths: str) -> str:
    """Get the full path to the cache file.

    :param libpaths: a cache file specific for the given library paths.
    """
    cache_name = get_cache_file_name(libpaths)
    folder = os.path.join(papis.utils.get_cache_home(), "database")
    if not os.path.exists(folder):
        os.makedirs(folder)

    return os.path.join(folder, cache_name)


def filter_documents(
        documents: List[papis.document.Document],
        search: str = "") -> List[papis.document.Document]:
    """Filter documents. It can be done in a multi core way.

    :param documents: List of Papis documents.
    :param search: Valid Papis search string.
    :returns: List of filtered documents

    >>> document = papis.document.from_data({'author': 'einstein'})
    >>> len(filter_documents([document], search="einstein")) == 1
    True
    >>> len(filter_documents([document], search="author : ein")) == 1
    True
    >>> len(filter_documents([document], search="title : ein")) == 1
    False

    """
    papis.docmatcher.DocMatcher.set_search(search)
    papis.docmatcher.DocMatcher.set_matcher(match_document)
    papis.docmatcher.DocMatcher.parse()

    logger.debug("Filtering %d docs (search '%s').", len(documents), search)

    import time
    begin_t = time.time()
    # FIXME: find a better solution for this that works for both OSes
    if sys.platform == "win32":
        filtered_docs = [
            d for d in [papis.docmatcher.DocMatcher.return_if_match(d)
                        for d in documents] if d is not None]
    else:
        result = papis.utils.parmap(papis.docmatcher.DocMatcher.return_if_match,
                                    documents)
        filtered_docs = [d for d in result if d is not None]

    delta = 1000 * (time.time() - begin_t)
    logger.debug("Finished filtering in %.2fms (%d docs).", delta, len(filtered_docs))

    return filtered_docs


def match_document(
        document: papis.document.Document,
        search: Pattern[str],
        match_format: Optional[AnyString] = None,
        doc_key: Optional[str] = None) -> Optional[Match[str]]:
    """Match a document's keys to a given search pattern.

    See ``papis.docmatcher.MatcherCallable``.

    >>> from papis.docmatcher import get_regex_from_search as regex
    >>> document = papis.document.from_data({'author': 'einstein'})
    >>> match_document(document, regex('e in'), '{doc[author]}') is None
    False
    >>> match_document(document, regex('ee in'), '{doc[author]}') is None
    True
    >>> match_document(document, regex('einstein'), '{doc[title]}') is None
    True
    """
    if doc_key is not None:
        match_string = str(document[doc_key])
    else:
        match_format = match_format or papis.config.getformattedstring("match-format")
        match_string = papis.format.format(match_format, document)

    return search.match(match_string)


class Database(papis.database.base.Database):

    def __init__(self, library: Optional[papis.library.Library] = None) -> None:
        super().__init__(library)

        self.documents: Optional[List[papis.document.Document]] = None
        self.initialize()

    def get_cache_path(self) -> str:
        return self._get_cache_file_path()

    def get_backend_name(self) -> str:
        return "papis"

    def initialize(self) -> None:
        pass

    def get_documents(self) -> List[papis.document.Document]:
        if self.documents is not None:
            return self.documents
        use_cache = papis.config.getboolean("use-cache")
        cache_path = self._get_cache_file_path()
        if use_cache and os.path.exists(cache_path):
            logger.debug("Getting documents from cache at '%s'.", cache_path)

            import pickle
            with open(cache_path, "rb") as fd:
                self.documents = pickle.load(fd)
        elif self.get_dirs():
            logger.info("Indexing library. This might take a while...")
            folders: List[str] = list(
                chain.from_iterable(papis.utils.get_folders(d) for d in self.get_dirs())
                )
            self.documents = papis.utils.folders_to_documents(folders)
            logger.debug("Computing 'papis_id' for each document.")
            for doc in self.documents:
                self.maybe_compute_id(doc)
            if use_cache:
                self.save()
        else:
            self.documents = []

        logger.debug("Loaded %d documents.", len(self.documents))
        return self.documents

    def add(self, document: papis.document.Document) -> None:
        logger.debug("Adding document: '%s'.", papis.document.describe(document))
        docs = self.get_documents()
        self.maybe_compute_id(document)
        docs.append(document)
        assert docs[-1].get_main_folder() == document.get_main_folder()
        folder = document.get_main_folder()
        assert folder is not None
        assert os.path.exists(folder)
        self.save()

    def update(self, document: papis.document.Document) -> None:
        if not papis.config.getboolean("use-cache"):
            return
        logger.debug("Updating document: '%s'.", papis.document.describe(document))

        docs = self.get_documents()
        result = self._locate_document(document)
        index = result[0][0]
        docs[index] = document
        self.save()

    def delete(self, document: papis.document.Document) -> None:
        if not papis.config.getboolean("use-cache"):
            return
        logger.debug("Deleting document: '%s'.", papis.document.describe(document))

        docs = self.get_documents()
        result = self._locate_document(document)
        index = result[0][0]
        docs.pop(index)
        self.save()

    def match(self,
              document: papis.document.Document,
              query_string: str) -> bool:
        from papis.docmatcher import get_regex_from_search
        query = get_regex_from_search(query_string)
        return bool(match_document(document, query))

    def clear(self) -> None:
        cache_path = self._get_cache_file_path()
        logger.warning("Clearing cache at '%s'.", cache_path)

        if os.path.exists(cache_path):
            os.remove(cache_path)

    def query_dict(self,
                   dictionary: Dict[str, str]) -> List[papis.document.Document]:
        query_string = " ".join(
            [f'{key}:"{val}" ' for key, val in dictionary.items()])
        return self.query(query_string)

    def query(self, query_string: str) -> List[papis.document.Document]:
        logger.debug("Querying database for '%s'.", query_string)

        docs = self.get_documents()
        # This makes it faster, if it's the all query string, return everything
        # without filtering
        if query_string == self.get_all_query_string():
            return docs
        else:
            return filter_documents(docs, query_string)

    def get_all_query_string(self) -> str:
        return "."

    def get_all_documents(self) -> List[papis.document.Document]:
        return self.get_documents()

    def save(self) -> None:
        docs = self.get_documents()
        logger.debug("Saving %d documents.", len(docs))

        import pickle
        path = self._get_cache_file_path()
        with open(path, "wb+") as fd:
            pickle.dump(docs, fd)

    def _get_cache_file_path(self) -> str:
        return get_cache_file_path(self.lib.path_format())

    def _locate_document(
            self,
            document: papis.document.Document
            ) -> List[Tuple[int, papis.document.Document]]:
        assert isinstance(document, papis.document.Document)

        result = list(filter(
            lambda d: d[1]["papis_id"] == document["papis_id"],
            enumerate(self.get_documents())))

        if result:
            return result

        result = list(filter(
            lambda d: d[1].get_main_folder() == document.get_main_folder(),
            enumerate(self.get_documents())))
        if not result:
            raise ValueError(
                "The document passed could not be found in the library: "
                f"'{papis.document.describe(document)}'")

        return result
