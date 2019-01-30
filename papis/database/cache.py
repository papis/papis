import logging
import os
import papis.utils
import papis.docmatcher
import papis.config
import papis.database.base
import re


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


def get(path):
    """Get contents stored in a cache file ``path`` in pickle binary format.

    :param path: Path to the cache file.
    :type  path: str
    :returns: Content of the cache file.
    :rtype: object

    >>> create([1,2,3], '/tmp/test-pickle')
    >>> get('/tmp/test-pickle')
    [1, 2, 3]
    """
    import pickle
    logger.debug("Getting cache %s " % path)
    return pickle.load(open(path, "rb"))


def create(obj, path):
    """Create a cache file in ``path`` with obj as its content using pickle
    binary format.

    :param obj: Any seriazable object.
    :type  obj: object
    :param path: Path to the cache file.
    :type  path: str
    :returns: Nothing
    :rtype: None
    """
    import pickle
    logger.debug("Saving in cache %s " % path)
    pickle.dump(obj, open(path, "wb+"))


def get_name(directory):
    """Create a cache file name out of the path of a given directory.

    :param directory: Folder name to be used as a seed for the cache name.
    :type  directory: str
    :returns: Name for the cache file.
    :rtype:  str

    >>> get_name('path/to/my/lib')
    'a8c689820a94babec20c5d6269c7d488-lib'
    >>> get_name('papers')
    'a566b2bebc62611dff4cdaceac1a7bbd-papers'
    """
    import hashlib
    return "{}-{}".format(
        hashlib.md5(directory.encode()).hexdigest(),
        os.path.basename(directory)
    )


def clear(directory):
    """Clear cache associated with a directory

    :param directory: Folder name that was used as a seed for the cache name.
    :type  directory: str
    :returns: Nothing
    :rtype: None

    >>> create([1,2,3], get_cache_file_path('some/other/papers'))
    >>> clear('some/other/papers')
    >>> import os; os.path.exists(get_cache_file_path('some/other/papers'))
    False
    >>> clear('non/existing/some/other/books')
    >>> os.path.exists(get_cache_file_path('non/existing/some/other/books'))
    False
    """
    directory = os.path.expanduser(directory)
    cache_path = get_cache_file_path(directory)
    if os.path.exists(cache_path):
        logger.debug("Clearing cache %s " % cache_path)
        os.remove(cache_path)


def clear_lib_cache(lib=None):
    """Clear cache associated with a library. If no library is given
    then the current library is used.

    :param lib: Library name.
    :type  lib: str

    >>> import os
    >>> if not os.path.exists('/tmp/setlib-test'): os.makedirs(\
            '/tmp/setlib-test'\
        )
    >>> papis.config.set_lib('/tmp/setlib-test')
    >>> create([1,2,3], get_cache_file_path('/tmp/setlib-test'))
    >>> os.path.exists(get_cache_file_path('/tmp/setlib-test'))
    True
    >>> clear_lib_cache('/tmp/setlib-test')
    >>> os.path.exists(get_cache_file_path('/tmp/setlib-test'))
    False
    """
    directory = papis.config.get("dir", section=lib)
    clear(directory)


def get_cache_file_path(directory):
    """Get the full path to the cache file

    :param directory: Library folder
    :type  directory: str

    >>> import os; os.environ["XDG_CACHE_HOME"] = '/tmp'
    >>> get_cache_file_path('blah/papers')
    '/tmp/papis/c39177eca0eaea2e21134b0bd06631b6-papers'
    """
    cache_name = get_name(directory)
    return os.path.expanduser(os.path.join(get_cache_home(), cache_name))


def get_folders(directory):
    """Get folders from within a containing folder from cache

    :param directory: Folder to look for documents (or library folder)
    :type  directory: str
    :param search: Valid papis search
    :type  search: str
    :returns: List of document objects.
    :rtype: list

    >>> create(['/a', '/b'], get_cache_file_path('/asdf/papers'))
    >>> get_folders('/asdf/papers')
    ['/a', '/b']

    """
    cache_home = get_cache_home()
    cache_path = get_cache_file_path(directory)
    folders = []
    logger.debug("Getting documents from dir %s" % directory)
    logger.debug("Cache path = %s" % cache_path)
    if not os.path.exists(cache_home):
        logger.debug("Creating cache dir %s " % cache_home)
        os.makedirs(cache_home, mode=papis.config.getint('dir-umask'))
    if os.path.exists(cache_path):
        logger.debug("Loading folders from cache")
        folders = get(cache_path)
    else:
        folders = papis.utils.get_folders(directory)
        create(folders, cache_path)
    return folders


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
        import multiprocessing
        import time
        np = papis.api.get_arg("cores", multiprocessing.cpu_count())
        pool = multiprocessing.Pool(np)
        logger.debug(
            "Filtering docs (search %s) using %s cores" % (
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
        logger.debug("pool done (%s ms)" % (1000*time.time()-1000*begin_t))
        return [d for d in result if d is not None]


def folders_to_documents(folders):
    """Turn folders into documents, this is done in a multiprocessing way, this
    step is quite critical for performance.

    :param folders: List of folder paths.
    :type  folders: list
    :returns: List of document objects.
    :rtype:  list
    """
    import multiprocessing
    import time
    logger = logging.getLogger("dir2doc")
    np = papis.api.get_arg("cores", multiprocessing.cpu_count())
    logger.debug("Running in %s cores" % np)
    pool = multiprocessing.Pool(np)
    logger.debug("pool started")
    begin_t = time.time()
    result = pool.map(papis.document.from_folder, folders)
    pool.close()
    pool.join()
    logger.debug("pool done (%s ms)" % (1000*time.time()-1000*begin_t))
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
        directory = os.path.expanduser(self.get_dir())

        if papis.config.getboolean("use-cache"):
            self.folders = get_folders(directory)
            self.logger.debug(
                "Loaded folders from cache ({} documents)".format(
                    len(self.folders)
                )
            )
        else:
            self.folders = papis.utils.get_folders(directory)

        self.logger.debug("Creating document objects")
        self.documents = folders_to_documents(self.folders)
        self.logger.debug("Done")

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
        self.logger.debug('Clearing library')
        clear_lib_cache(self.get_lib())

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
        self.logger.debug(
            'Saving ... ({} documents)'.format(len(self.folders))
        )
        create(self.folders, get_cache_file_path(self.get_dir()))
