import os
import shutil
import papis.utils
import papis.config
import papis.bibtex
import logging


logger = logging.getLogger("document")


def open_in_browser(document):
    """Browse document's url whenever possible.

    :document: Document object
    :returns: Returns the url that is composed from the document
    :rtype:  str

    >>> import papis.config; papis.config.set('browser', 'echo')
    >>> papis.config.set('browse-key', 'url')
    >>> open_in_browser( from_data({'url': 'hello.com'}) )
    'hello.com'
    >>> papis.config.set('browse-key', 'doi')
    >>> open_in_browser( from_data({'doi': '12312/1231'}) )
    'https://doi.org/12312/1231'
    >>> papis.config.set('browse-key', 'nonexistentkey')
    >>> open_in_browser( from_data({'title': 'blih', 'author': 'me'}) )
    'https://duckduckgo.com/?q=blih+me'
    """
    global logger
    url = None
    key = papis.config.get("browse-key")

    if document.has(key):
        if "doi" == key:
            url = 'https://doi.org/{}'.format(document['doi'])
        elif "isbn" == key:
            url = 'https://isbnsearch.org/isbn/{}'.format(document['isbn'])
        else:
            url = document[key]

    if url is None or key == 'search-engine':
        from urllib.parse import urlencode
        params = {
            'q': papis.utils.format_doc(
                papis.config.get('browse-query-format'),
                document
            )
        }
        url = papis.config.get('search-engine') + '/?' + urlencode(params)

    logger.debug("Opening url %s:" % url)
    papis.utils.general_open(
        url, "browser", wait=False
    )
    return url


def from_folder(folder_path):
    """Construct a document object from a folder

    :param folder_path: Full path to a valid papis folder
    :type  folder_path: str
    :returns: A papis document
    :rtype:  papis.document.Document
    """
    return papis.document.Document(folder=folder_path)


def from_data(data):
    """Construct a document object from a data dictionary.

    :param data: Data to be copied to a new document
    :type  data: dict
    :returns: A papis document
    :rtype:  papis.document.Document
    """
    return papis.document.Document(data=data)


def to_bibtex(document):
    """Create a bibtex string from document's information

    :param document: Papis document
    :type  document: Document
    :returns: String containing bibtex formating
    :rtype:  str

    >>> import papis.config
    >>> papis.config.set('bibtex-journal-key', 'journal_abbrev')
    >>> doc = from_data({'title': 'Hello', 'type': 'book', 'journal': 'jcp'})
    >>> import tempfile; doc.set_folder('path/to/superfolder')
    >>> to_bibtex(doc)
    '@book{superfolder,\\n  journal = { jcp },\\n  title = { Hello },\\n  type = { book },\\n}\\n'
    >>> doc['journal_abbrev'] = 'j'
    >>> to_bibtex(doc)
    '@book{superfolder,\\n  journal = { j },\\n  title = { Hello },\\n  type = { book },\\n}\\n'
    >>> del doc['title']
    >>> doc['ref'] = 'hello1992'
    >>> to_bibtex(doc)
    '@book{hello1992,\\n  journal = { j },\\n  type = { book },\\n}\\n'
    """
    bibtexString = ""
    bibtexType = ""

    # First the type, article ....
    if "type" in document.keys():
        if document["type"] in papis.bibtex.bibtex_types:
            bibtexType = document["type"]
    if not bibtexType:
        bibtexType = "article"

    ref = document["ref"]
    if not ref:
        try:
            ref = os.path.basename(document.get_main_folder())
        except:
            if document.has('doi'):
                ref = document['doi']
            else:
                ref = 'noreference'

    bibtexString += "@%s{%s,\n" % (bibtexType, ref)
    for bibKey in papis.bibtex.bibtex_keys:
        if bibKey in document.keys():
            if bibKey == 'journal':
                bibtex_journal_key = papis.config.get('bibtex-journal-key')
                if bibtex_journal_key in document.keys():
                    bibtexString += "  %s = { %s },\n" % (
                        'journal',
                        papis.bibtex.unicode_to_latex(
                            str(
                              document[papis.config.get('bibtex-journal-key')]
                            )
                        )
                    )
                elif bibtex_journal_key not in document.keys():
                    logger.warning(
                        "Key '%s' is not present for ref=%s" % (
                            papis.config.get('bibtex-journal-key'),
                            document["ref"]
                        )
                    )
                    bibtexString += "  %s = { %s },\n" % (
                        'journal',
                        papis.bibtex.unicode_to_latex(
                            str(document['journal'])
                        )
                    )
            else:
                bibtexString += "  %s = { %s },\n" % (
                    bibKey,
                    papis.bibtex.unicode_to_latex(
                        str(document[bibKey])
                    )
                )
    bibtexString += "}\n"
    return bibtexString


def to_json(document):
    """Export information into a json string
    :param document: Papis document
    :type  document: Document
    :returns: Json formatted info file
    :rtype:  str

    >>> doc = from_data({'title': 'Hello World'})
    >>> to_json(doc)
    '{"title": "Hello World"}'
    """
    import json
    return json.dumps(to_dict(document))


def to_dict(document):
    """Gets a python dictionary with the information of the document
    :param document: Papis document
    :type  document: Document
    :returns: Python dictionary
    :rtype:  dict
    """
    result = dict()
    for key in document.keys():
        result[key] = document[key]
    return result


def dump(document):
    """Return information string without any obvious format
    :param document: Papis document
    :type  document: Document
    :returns: String with document's information
    :rtype:  str

    >>> doc = from_data({'title': 'Hello World'})
    >>> dump(doc)
    'title:   Hello World\\n'
    """
    string = ""
    for i in document.keys():
        string += str(i)+":   "+str(document[i])+"\n"
    return string


def delete(document):
    """This function deletes a document from disk.
    :param document: Papis document
    :type  document: papis.document.Document
    """
    import shutil
    folder = document.get_main_folder()
    shutil.rmtree(folder)


def move(document, path):
    """This function moves a document to path, it supposes that
    the document exists in the location ``document.get_main_folder()``.
    Warning: This method will change the folder in the document object too.
    :param document: Papis document
    :type  document: papis.document.Document
    :param path: Full path where the document will be moved to
    :type  path: str

    >>> doc = from_data({'title': 'Hello World'})
    >>> doc.set_folder('path/to/folder')
    >>> import tempfile; newfolder = tempfile.mkdtemp()
    >>> move(doc, newfolder)
    Traceback (most recent call last):
    ...
    Exception: Path ... exists already
    """
    import shutil
    path = os.path.expanduser(path)
    if os.path.exists(path):
        raise Exception("Path {} exists already".format(path))
    shutil.move(document.get_main_folder(), path)
    # Let us chmod it because it might come from a temp folder
    # and temp folders are per default 0o600
    os.chmod(path, papis.config.getint('dir-umask'))
    document.set_folder(path)


class DocHtmlEscaped(dict):
    """
    Small helper class to escape html elements.

    >>> DocHtmlEscaped(from_data(dict(title='> >< int & "" "')))['title']
    '&gt; &gt;&lt; int &amp; &quot;&quot; &quot;'
    """

    def __init__(self, doc):
        self.doc = doc

    def __getitem__(self, key):
        return str(self.doc[key]).replace('&', '&amp;')\
                                .replace('<', '&lt;')\
                                .replace('>', '&gt;')\
                                .replace('"', '&quot;')


class Document(object):

    """Class implementing the entry abstraction of a document in a library.
    It is basically a python dictionary with more methods.
    """

    subfolder = ""
    _infoFilePath = ""

    def __init__(self, folder=None, data=None):
        self._keys = []
        self._folder = None

        if folder is not None:
            self.set_folder(folder)
            self.load()

        if data is not None:
            self.update(data)

    def __delitem__(self, key):
        """Deletes property from document, e.g. ``del doc['url']``.
        :param key: Name of the property.
        :type  key: str

        >>> doc = from_data({'title': 'Hello', 'type': 'book'})
        >>> del doc['title']
        >>> doc.has('title')
        False
        """
        self._keys.pop(self._keys.index(key))
        delattr(self, key)

    def __setitem__(self, key, value):
        """Sets property to value from document, e.g. ``doc['url'] =
        'www.gnu.org'``.
        :param key: Name of the property.
        :type  key: str
        :param value: Value of the parameter
        :type  value: str,int,float,list
        """
        self._keys.append(key)
        setattr(self, key, value)

    def __getitem__(self, key):
        """Gets property to value from document, e.g. ``a = doc['url']``.
        If the property `key` does not exist, then the empy string is returned.

        :param key: Name of the property.
        :type  key: str
        :returns: Value of the property
        :rtype:  str,int,float,list
        """
        return getattr(self, key) if hasattr(self, key) else ""

    @property
    def html_escape(self):
        return DocHtmlEscaped(self)

    def get_main_folder(self):
        """Get full path for the folder where the document and the information
        is stored.
        :returns: Folder path
        """
        return self._folder

    def set_folder(self, folder):
        """Set document's folder. The info_file path will be accordingly set.

        :param folder: Folder where the document will be stored, full path.
        :type  folder: str
        """
        self._folder = folder
        self._infoFilePath = os.path.join(
            folder,
            papis.utils.get_info_file_name()
        )
        self.subfolder = self.get_main_folder().replace(
            os.environ["HOME"], ""
        ).replace(
            "/", " "
        )

    def get_main_folder_name(self):
        """Get main folder name where the document and the information is
        stored.
        :returns: Folder name
        """
        return os.path.basename(self._folder)

    def has(self, key):
        """Check if the information file has some key defined.

        :param key: Key name to be checked
        :returns: True/False

        >>> doc = from_data({'title': 'Hello World'})
        >>> doc.has('title')
        True
        >>> doc.has('author')
        False
        """
        return key in self.keys()

    def rm_file(self, filepath):
        """Remove file from document, it also removes the entry in `files`

        :filepath: Full file path for file

        >>> doc = from_data({'title': 'Hello', 'files': ['a.pdf']})
        >>> doc.rm_file('b.pdf')
        Traceback (most recent call last):
        ...
        Exception: File b.pdf not tracked by document
        """
        basename = os.path.basename(filepath)
        if basename not in self['files']:
            raise Exception("File %s not tracked by document" % basename)
        os.remove(filepath)
        self['files'].pop(self['files'].index(basename))

    def rm(self):
        """Removes document's folder, effectively removing it from the library.

        >>> doc = from_data({'title': 'Hello World'})
        >>> import tempfile; doc.set_folder(tempfile.mkdtemp())
        >>> doc.rm()
        """
        shutil.rmtree(self.get_main_folder())

    def save(self):
        """Saves the current document's information into the info file.
        """
        import yaml
        fd = open(self._infoFilePath, "w+")
        structure = dict()
        for key in self.keys():
            structure[key] = self[key]
        # self.logger.debug("Saving %s " % self.get_info_file())
        yaml.dump(
            structure,
            fd,
            allow_unicode=papis.config.getboolean("info-allow-unicode"),
            default_flow_style=False
        )
        fd.close()

    def update(self, data, force=False, interactive=False):
        """Update document's information from an info dictionary.

        :param data: Dictionary with key and values to be updated
        :type  data: dict
        :param force: If True, the update turns into a replace, i.e., it
            replaces the old value by the new value stored in data.
        :type  force: bool
        :param interactive: If True, it will ask for user's input every time
            that the values differ.
        :type  interactive: bool

        """
        for key in data.keys():
            if self[key] != data[key]:
                if force:
                    self[key] = data[key]
                elif interactive:
                    confirmation = papis.utils.confirm(
                        "(%s conflict) Replace '%s' by '%s'?" % (
                            key, self[key], data[key]
                        )
                    )
                    if confirmation:
                        self[key] = data[key]
                elif self[key] is None or self[key] == '':
                    self[key] = data[key]

    def get_info_file(self):
        """Get full path for the info file
        :returns: Full path for the info file
        :rtype: str
        """
        return self._infoFilePath

    def get_files(self):
        """Get the files linked to the document, if any.

        :returns: List of full file paths
        :rtype:  list
        """
        files = self["files"] if isinstance(self["files"], list) \
            else [self["files"]]
        result = []
        for f in files:
            result.append(os.path.join(self.get_main_folder(), f))
        return result

    def keys(self):
        """Returns the keys defined for the document.

        :returns: Keys for the document
        :rtype:  list
        """
        return self._keys

    @property
    def has_citations(self):
        """Returns string defined in config if keys contains citations
        else returns None.

        :returns: String or None
        :rtype: str OR None

        >>> import papis.config
        >>> doc = from_data({'title': 'Hello World'})
        >>> doc.has_citations
        ''
        >>> doc.update(dict(citations=[]))
        >>> doc.has_citations == papis.config.get('citation-string')
        True
        """

        if 'citations' in self.keys():
            return papis.config.get('citation-string')
        else:
            return ''

    def dump(self):
        """Return information string without any obvious format
        :returns: String with document's information
        :rtype:  str

        >>> doc = from_data({'title': 'Hello World'})
        >>> doc.dump()
        'title:   Hello World\\n'
        """
        return dump(self)

    def load(self):
        """Load information from info file
        """
        import yaml
        # TODO: think about if it's better to raise an exception here
        # TODO: if no info file is found
        try:
            fd = open(self.get_info_file(), "r")
        except:
            return False
        try:
            structure = yaml.load(fd)
            for key in structure:
                self[key] = structure[key]
            fd.close()
        except Exception as e:
            logging.error(
                'Error reading yaml file in {0}'.format(self.get_info_file()) +
                '\nPlease check it!\n\n{0}'.format(str(e))
            )
            fd.close()
