import os
import re

import papis.config
import papis.logging
from papis.database.base import Database as DatabaseBase, get_cache_file_path
from papis.document import Document, describe
from papis.exceptions import DocumentFolderNotFound
from papis.library import Library
from papis.strings import AnyString

logger = papis.logging.get_logger(__name__)


def filter_documents(documents: list[Document], search: str = "") -> list[Document]:
    """Filter documents based on the *search* string.

    :param search: a search string that will be parsed by
        :class:`~papis.docmatcher.DocMatcher`.
    :returns: a list of filtered documents.

    >>> document = papis.document.from_data({'author': 'einstein'})
    >>> len(filter_documents([document], search="einstein")) == 1
    True
    >>> len(filter_documents([document], search="author : ein")) == 1
    True
    >>> len(filter_documents([document], search="title : ein")) == 1
    False

    """
    from papis.docmatcher import DocMatcher

    DocMatcher.set_search(search)
    DocMatcher.set_matcher(match_document)
    DocMatcher.parse()

    logger.debug("Filtering %d docs (search '%s').", len(documents), search)

    import sys
    import time

    t_start = time.time()

    # FIXME: find a better solution for this that works for both OSes
    if sys.platform == "win32":
        filtered_docs = [
            d for d in (DocMatcher.return_if_match(d) for d in documents)
            if d is not None]
    else:
        from papis.utils import parmap

        result = parmap(DocMatcher.return_if_match, documents)
        filtered_docs = [d for d in result if d is not None]

    t_delta = 1000 * (time.time() - t_start)
    logger.debug("Finished querying in %.2fms (%d docs).", t_delta, len(filtered_docs))

    return filtered_docs


def match_document(
        document: Document,
        search: re.Pattern[str],
        match_format: AnyString | None = None,
        doc_key: str | None = None) -> re.Match[str] | None:
    """Match a document's keys to a given search pattern.

    See :class:`~papis.docmatcher.MatcherCallable`.

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
        from papis.format import format

        match_format = match_format or papis.config.getformatpattern("match-format")
        match_string = format(match_format, document)

    return search.match(match_string)


class Database(DatabaseBase):
    """A caching database backend for Papis based on :mod:`pickle`."""

    def __init__(self, library: Library | None = None) -> None:
        super().__init__(library)

        self.use_cache = papis.config.getboolean("use-cache")
        self.documents: list[Document] | None = None
        self.initialize()

    def get_backend_name(self) -> str:  # noqa: PLR6301
        return "papis"

    def get_cache_path(self) -> str:
        return self._get_cache_file_path()

    def get_all_query_string(self) -> str:  # noqa: PLR6301
        return "."

    def initialize(self) -> None:
        # NOTE: ensure that all the documents are loaded on initialize to match
        # the behaviour of the whoosh backend
        _ = self._get_documents()

    def clear(self) -> None:
        cache_path = self._get_cache_file_path()
        if os.path.exists(cache_path):
            logger.info("Clearing cache at '%s'.", cache_path)
            os.remove(cache_path)

        if self.documents:
            self.documents.clear()
            self.documents = None

    def add(self, document: Document) -> None:
        if not self.use_cache:
            return

        folder = document.get_main_folder()
        if folder is None:
            raise ValueError("Cannot add a document without a main folder to database")

        if not os.path.exists(folder):
            raise ValueError(f"Document folder '{folder}' does not exist")

        logger.debug("Adding document: '%s'.", describe(document))
        docs = self._get_documents()

        self.maybe_compute_id(document)
        docs.append(document)

        self._save_documents()

    def update(self, document: Document) -> None:
        if not self.use_cache:
            return

        logger.debug("Updating document: '%s'.", describe(document))

        docs = self._get_documents()
        result = self._locate_document(document)
        if not result:
            raise DocumentFolderNotFound(describe(document))

        index, _ = result[0]
        docs[index] = document
        self._save_documents()

    def delete(self, document: Document) -> None:
        if not self.use_cache:
            return

        logger.debug("Deleting document: '%s'.", describe(document))

        docs = self._get_documents()
        result = self._locate_document(document)
        if not result:
            raise DocumentFolderNotFound(describe(document))

        index, _ = result[0]
        docs.pop(index)
        self._save_documents()

    def query(self, query_string: str) -> list[Document]:
        logger.debug("Querying database for '%s'.", query_string)

        docs = self._get_documents()
        if query_string == self.get_all_query_string():
            return docs

        return filter_documents(docs, query_string)

    def query_dict(self, query: dict[str, str]) -> list[Document]:
        query_string = " ".join(f'{key}:"{val}" ' for key, val in query.items())
        return self.query(query_string)

    def get_all_documents(self) -> list[Document]:
        return self._get_documents()

    def _get_documents(self) -> list[Document]:
        if self.documents is not None:
            return self.documents

        cache_path = self._get_cache_file_path()
        if self.use_cache and os.path.exists(cache_path):
            logger.debug("Getting documents from cache at '%s'.", cache_path)

            import pickle
            with open(cache_path, "rb") as fd:
                self.documents = pickle.load(fd)
        elif self.lib.paths:
            from papis.utils import folders_to_documents, get_folders

            logger.info("Indexing library. This might take a while...")
            folders = [f for path in self.lib.paths for f in get_folders(path)]
            self.documents = folders_to_documents(folders)

            from papis.id import ID_KEY_NAME
            logger.debug("Computing '%s' for each document.", ID_KEY_NAME)

            for doc in self.documents:
                self.maybe_compute_id(doc)

            if self.use_cache:
                self._save_documents()
        else:
            self.documents = []

        logger.debug("Loaded %d documents.", len(self.documents))
        return self.documents

    def _save_documents(self) -> None:
        docs = self._get_documents()
        logger.debug("Saving %d documents.", len(docs))

        import pickle
        path = self._get_cache_file_path()
        with open(path, "wb+") as fd:
            pickle.dump(docs, fd)

    def _get_cache_file_path(self) -> str:
        return get_cache_file_path(self.lib.path_format())

    def _locate_document(self, document: Document) -> list[tuple[int, Document]]:
        from papis.id import ID_KEY_NAME

        # FIXME: Why are we iterating twice over the documents here?
        # first try to match by ID
        result = [
            (i, doc) for i, doc in enumerate(self._get_documents())
            if doc[ID_KEY_NAME] == document[ID_KEY_NAME]
        ]
        if result:
            return result

        # if no documents match, try matching by main folder
        result = [
            (i, doc) for i, doc in enumerate(self._get_documents())
            if doc.get_main_folder() == document.get_main_folder()
        ]
        if result:
            return result

        # otherwise, we error
        raise ValueError(
            f"Document could not be found in the library '{self.lib.name}': "
            f"'{describe(document)}'")
