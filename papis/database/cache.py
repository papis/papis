import pickle
import logging
import os
import papis.utils
import papis.docmatcher
import papis.config
import papis.database.base
import re
import multiprocessing
import time


logger = logging.getLogger("cache")


def get_cache_home():
    """Get folder where the cache files are stored, it retrieves the
    ``cache-dir`` configuration setting. It is ``XDG`` standard compatible.

    :returns: Full path for cache main folder
    :rtype:  str

    >>> import os; os.environ["XDG_CACHE_HOME"] = '~/.cache'
    >>> get_cache_home() == os.path.expanduser(\
            os.path.join(os.environ["XDG_CACHE_HOME"], 'papis')\
        )
    True
    >>> os.environ["XDG_CACHE_HOME"] = '/tmp/.cache'
    >>> get_cache_home()
    '/tmp/.cache/papis'
    >>> del os.environ["XDG_CACHE_HOME"]
    >>> get_cache_home() == os.path.expanduser(\
            os.path.join('~/.cache', 'papis')\
        )
    True
    """
    user_defined = papis.config.get('cache-dir')
    if user_defined is not None:
        return os.path.expanduser(user_defined)
    else:
        return os.path.expanduser(
            os.path.join(os.environ.get('XDG_CACHE_HOME'), 'papis')
        ) if os.environ.get(
            'XDG_CACHE_HOME'
        ) else os.path.expanduser(
            os.path.join('~', '.cache', 'papis')
        )


def get_cache_file_name(directory):
    """Create a cache file name out of the path of a given directory.

    :param directory: Folder name to be used as a seed for the cache name.
    :type  directory: str
    :returns: Name for the cache file.
    :rtype:  str

    >>> get_cache_file_name('path/to/my/lib')
    'a8c689820a94babec20c5d6269c7d488-lib'
    >>> get_cache_file_name('papers')
    'a566b2bebc62611dff4cdaceac1a7bbd-papers'
    """
    import hashlib
    return "{}-{}".format(
        hashlib.md5(directory.encode()).hexdigest(),
        os.path.basename(directory)
    )


def get_cache_file_path(directory):
    """Get the full path to the cache file

    :param directory: Library folder
    :type  directory: str

    >>> import os; os.environ["XDG_CACHE_HOME"] = '/tmp'
    >>> get_cache_file_path('blah/papers')
    '/tmp/papis/c39177eca0eaea2e21134b0bd06631b6-papers'
    """
    cache_name = get_cache_file_name(directory)
    return os.path.expanduser(os.path.join(get_cache_home(), cache_name))



def filter_documents(documents, search=""):
    """Filter documents. It can be done in a multi core way.

    :param documents: List of papis documents.
    :type  documents: papis.documents.Document
    :param search: Valid papis search string.
    :type  search: str
    :returns: List of filtered documents
    :rtype:  list

    >>> document = papis.document.from_data({'author': 'einstein'})
    >>> len(filter_documents([document], search="einstein")) == 1
    True
    >>> len(filter_documents([document], search="author = ein")) == 1
    True
    >>> len(filter_documents([document], search="title = ein")) == 1
    False

    """
    logger = logging.getLogger('filter')
    papis.docmatcher.DocMatcher.set_search(search)
    papis.docmatcher.DocMatcher.parse()
    papis.docmatcher.DocMatcher.set_matcher(match_document)
    if search == "" or search == ".":
        return documents
    else:
        # Doing this multiprocessing in filtering does not seem
        # to help much, I don't know if it's because I'm doing something
        # wrong or it is really like this.
        np = papis.api.get_arg("cores", multiprocessing.cpu_count())
        pool = multiprocessing.Pool(np)
        logger.debug(
            "Filtering {} docs (search {}) using {} cores".format(
                len(documents),
                search,
                np
            )
        )
        logger.debug("pool started")
        begin_t = time.time()
        result = pool.map(
            papis.docmatcher.DocMatcher.return_if_match, documents
        )
        pool.close()
        pool.join()
        filtered_docs = [d for d in result if d is not None]
        logger.debug(
            "done ({} ms) ({} docs)".format(
                1000*time.time()-1000*begin_t,
                len(filtered_docs))
        )
        return filtered_docs


def folders_to_documents(folders):
    """Turn folders into documents, this is done in a multiprocessing way, this
    step is quite critical for performance.

    :param folders: List of folder paths.
    :type  folders: list
    :returns: List of document objects.
    :rtype:  list
    """
    logger = logging.getLogger("db:cache:dir2doc")
    np = papis.api.get_arg("cores", multiprocessing.cpu_count())
    logger.debug("converting folder into documents on {0} cores".format(np))
    pool = multiprocessing.Pool(np)
    begin_t = time.time()
    result = pool.map(papis.document.from_folder, folders)
    pool.close()
    pool.join()
    logger.debug("done in %.1f ms" % (1000*time.time()-1000*begin_t))
    return result


def match_document(document, search, match_format=None):
    """Main function to match document to a given search.

    :param document: Papis document
    :type  document: papis.document.Document
    :param search: A valid search string
    :type  search: str
    :param match_format: Python-like format string.
        (`see <
            https://docs.python.org/2/library/string.html#format-string-syntax
        >`_)
    :type  match_format: str
    :returns: Non false if matches, true-ish if it does match.

    >>> papis.config.set('match-format', '{doc[author]}')
    >>> document = papis.document.from_data({'author': 'einstein'})
    >>> match_document(document, 'e in') is None
    False
    >>> match_document(document, 'ee in') is None
    True
    >>> match_document(document, 'einstein', '{doc[title]}') is None
    True
    """
    match_format = match_format or papis.config.get("match-format")
    match_string = papis.utils.format_doc(match_format, document)
    regex = get_regex_from_search(search)
    return re.match(regex, match_string, re.IGNORECASE)


def get_regex_from_search(search):
    """Creates a default regex from a search string.

    :param search: A valid search string
    :type  search: str
    :returns: Regular expression
    :rtype: str

    >>> get_regex_from_search(' ein 192     photon')
    '.*.*ein.*192.*photon'
    """
    return r".*"+re.sub(r"\s+", ".*", search)


class Database(papis.database.base.Database):

    def __init__(self, library=None):
        papis.database.base.Database.__init__(self, library)
        self.logger = logging.getLogger('db:cache')
        self.logger.debug('Initializing')
        self.documents = []
        self.folders = []
        self.initialize()

    def get_backend_name(self):
        return 'papis'

    def initialize(self):
        self.get_documents()

    def get_documents(self):
        directory = os.path.expanduser(self.get_dirs()[0])
        use_cache = papis.config.getboolean("use-cache")
        self.folders = self._get_paths(use_cache=use_cache)
        self.logger.debug(
            "Loaded folders ({} documents)".format(
                len(self.folders)
            )
        )

        self.documents = folders_to_documents(self.folders)

    def add(self, document):
        self.logger.debug('Adding ...')
        self.folders.append(document.get_main_folder())
        assert(self.folders[-1] == document.get_main_folder())
        assert(os.path.exists(document.get_main_folder()))
        self.documents.append(document)
        self.save()

    def update(self, document):
        self.logger.debug('Updating document')

    def delete(self, document):
        if papis.config.getboolean("use-cache"):
            self.logger.debug(
                'Deleting ... ({} documents)'.format(len(self.folders))
            )
            self.folders.remove(document.get_main_folder())
            self.save()
            # Also update the documents list
            self.get_documents()

    def match(self, document, query_string):
        return match_document(document, query_string)

    def clear(self):
        cache_path = self._get_cache_file_path()
        self.logger.warning("clearing cache %s " % cache_path)
        if os.path.exists(cache_path):
            os.remove(cache_path)


    def query_dict(self, dictionary):
        query_string = " ".join(
            ["{}=\"{}\" ".format(key, val) for key, val in dictionary.items()]
        )
        return self.query(query_string)

    def query(self, query_string):
        self.logger.debug('Querying')
        if len(self.documents) == 0:
            self.get_documents()
        return filter_documents(self.documents, query_string)

    def get_all_query_string(self):
        return '.'

    def get_all_documents(self):
        return self.query(self.get_all_query_string())

    def save(self):

        cache_home = get_cache_home()
        if not os.path.exists(cache_home):
            self.logger.debug("Creating cache dir %s " % cache_home)
            os.makedirs(cache_home, mode=papis.config.getint('dir-umask'))

        self.logger.debug(
            'Saving ... ({} documents)'.format(len(self.folders))
        )
        path = self._get_cache_file_path()
        with open(path, "wb+") as fd:
            pickle.dump(self.folders, fd)

    def _get_cache_file_path(self):
        return get_cache_file_path(self.lib.path_format())

    def _get_paths(self, use_cache=True):
        cache_path = self._get_cache_file_path()
        folders = []
        if use_cache and os.path.exists(cache_path):
            logger.debug("Loading folders from cache")
            with open(cache_path, 'rb') as fd:
                return pickle.load(fd)
        else:
            return sum([
                papis.utils.get_folders(d) for d in self.get_dirs()
            ], [])

