import os
import papis.utils
import papis.config
import papis.bibtex
import logging
import re
import shutil


logger = logging.getLogger("document")


def new(folder_path, data, files=[]):
    """
    Creates a document at a given folder with data and
    some existing files.

    :param folder_path: A folder path, if non existing it will be created
    :type  folder_path: str
    :param data: Dictionary with key and values to be updated
    :type  data: dict
    :param files: Existing paths for files
    :type  files: list(str)
    :raises FileExistsError: If folder_path exists
    """
    assert(isinstance(folder_path, str))
    assert(isinstance(data, dict))
    assert(isinstance(files, list))
    os.makedirs(folder_path)
    doc = Document(folder=folder_path, data=data)
    doc['files'] = []
    for f in files:
        shutil.copy(f, os.path.join(folder_path))
        doc['files'].append(os.path.basename(f))
    doc.save()
    return doc


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

    """
    logger = logging.getLogger("document:bibtex")
    bibtexString = ""
    bibtexType = ""

    # First the type, article ....
    if "type" in document.keys():
        if document["type"] in papis.bibtex.bibtex_types:
            bibtexType = document["type"]
        elif document["type"] in papis.bibtex.bibtex_type_converter.keys():
            bibtexType = papis.bibtex.bibtex_type_converter[document["type"]]
    if not bibtexType:
        bibtexType = "article"

    # REFERENCE BUILDING
    if document.has("ref"):
        ref = document["ref"]
    elif papis.config.get('ref-format'):
        try:
            ref = papis.utils.format_doc(
                papis.config.get("ref-format"),
                document
            ).replace(" ", "")
        except Exception as e:
            logger.error(e)
            ref = None

    logger.debug("generated ref=%s" % ref)
    if not ref:
        if document.has('doi'):
            ref = document['doi']
        else:
            try:
                ref = os.path.basename(document.get_main_folder())
            except:
                ref = 'noreference'

    ref = re.sub(r'[;,()\/{}\[\]]', '', ref)
    logger.debug("Used ref=%s" % ref)

    bibtexString += "@{type}{{{ref},\n".format(type=bibtexType, ref=ref)
    for bibKey in sorted(document.keys()):
        logger.debug('%s : %s' % (bibKey, document[bibKey]))
        if bibKey in papis.bibtex.bibtex_key_converter:
            newBibKey = papis.bibtex.bibtex_key_converter[bibKey]
            document[newBibKey] = document[bibKey]
            continue
        if bibKey in papis.bibtex.bibtex_keys:
            value = str(document[bibKey])
            if not papis.config.get('bibtex-unicode'):
                value = papis.bibtex.unicode_to_latex(value)
            if bibKey == 'journal':
                bibtex_journal_key = papis.config.get('bibtex-journal-key')
                if bibtex_journal_key in document.keys():
                    bibtexString += "  %s = {%s},\n" % (
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
                    bibtexString += "  %s = {%s},\n" % (
                        'journal',
                        value
                    )
            else:
                bibtexString += "  %s = {%s},\n" % (
                    bibKey,
                    value
                )
    bibtexString += "}\n"
    return bibtexString


def to_json(document):
    """Export information into a json string
    :param document: Papis document
    :type  document: Document
    :returns: Json formatted info file
    :rtype:  str

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
    folder = document.get_main_folder()
    shutil.rmtree(folder)


def describe(document):
    """Return a string description of the current document
    using the document-description-format
    """
    return papis.utils.format_doc(
        papis.config.get('document-description-format'),
        document
    )


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
    Exception: There is already...
    """
    path = os.path.expanduser(path)
    if os.path.exists(path):
        raise Exception(
            "There is already a document in {0}, please check it,\n"
            "a temporary papis document has been stored in {1}".format(
                path, document.get_main_folder()
            )
        )
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
        self.__doc = doc

    def __getitem__(self, key):
        return (
            str(self.__doc[key])
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
        )


class Document(object):

    """Class implementing the entry abstraction of a document in a library.
    It is basically a python dictionary with more methods.
    """

    subfolder = ""
    _info_file_path = ""

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

        """
        self._keys.remove(key)
        delattr(self, key)

    def __setitem__(self, key, value):
        """Sets property to value from document, e.g. ``doc['url'] =
        'www.gnu.org'``.
        :param key: Name of the property.
        :type  key: str
        :param value: Value of the parameter
        :type  value: str,int,float,list
        """
        if key not in self._keys:
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
        self._info_file_path = os.path.join(
            folder,
            papis.config.get('info-name')
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

        """
        return key in self.keys()

    def save(self):
        """Saves the current document's information into the info file.
        """
        import papis.yaml
        papis.yaml.data_to_yaml(
            self.get_info_file(),
            {key: self[key] for key in self.keys() if self[key]}
        )

    def get_info_file(self):
        """Get full path for the info file
        :returns: Full path for the info file
        :rtype: str
        """
        return self._info_file_path

    def get_files(self):
        """Get the files linked to the document, if any.

        :returns: List of full file paths
        :rtype:  list
        """
        result = []
        if not self.has('files'):
            return result
        files = (
            self["files"] if isinstance(self["files"], list)
            else [self["files"]]
        )
        for f in files:
            result.append(os.path.join(self.get_main_folder(), f))
        return result

    def update(self, data):
        """Update document's information from an info dictionary.

        :param data: Dictionary with key and values to be updated
        :type  data: dict

        """
        for key in data.keys():
            self[key] = data[key]

    def keys(self):
        """Returns the keys defined for the document.

        :returns: Keys for the document
        :rtype:  list
        """
        return self._keys

    def load(self):
        """Load information from info file
        """
        import papis.yaml
        if not os.path.exists(self.get_info_file()):
            return
        data = papis.yaml.yaml_to_data(self.get_info_file())
        for key in data:
            self[key] = data[key]
