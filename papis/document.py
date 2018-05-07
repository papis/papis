import os
import sys
import shutil
import papis.utils
import papis.config
import papis.bibtex

import logging
logger = logging.getLogger("document")

def open_in_browser(document):
    """Browse document's url whenever possible.

    :document: Document object

    """
    global logger
    url = None
    if "url" in document.keys():
        url = document["url"]
    elif 'doi' in document.keys():
        url = 'https://doi.org/' + document['doi']
    elif papis.config.get('doc-url-key-name') in document.keys():
        url = document[papis.config.get('doc-url-key-name')]
    else:
        from urllib.parse import urlencode
        params = {
            'q': papis.utils.format_doc(
                papis.config.get('browse-query-format'),
                document
            )
        }
        url = papis.config.get('search-engine') + '/?' + urlencode(params)

    if url is None:
        logger.warning(
            "No url for %s possible" % (document.get_main_folder_name())
        )
    else:
        logger.debug("Opening url %s:" % url)
        papis.utils.general_open(
            url, "browser", wait=False
        )


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
    bibtexString = ""
    bibtexType = ""
    # First the type, article ....
    if "type" in document.keys():
        if document["type"] in papis.bibtex.bibtex_types:
            bibtexType = document["type"]
    if not bibtexType:
        bibtexType = "article"
    if not document["ref"]:
        ref = os.path.basename(document.get_main_folder())
    else:
        ref = document["ref"]
    bibtexString += "@%s{%s,\n" % (bibtexType, ref)
    for bibKey in papis.bibtex.bibtex_keys:
        if bibKey in document.keys():
            bibtexString += "  %s = { %s },\n" % (
                bibKey, papis.bibtex.unicode_to_latex(str(document[bibKey]))
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
        """
        return key in self.keys()

    def check_files(self):
        """Check for the exsitence of the document's files
        :returns: False if some file does not exist, True otherwise
        :rtype:  bool
        """
        for f in self.get_files():
            # self.logger.debug(f)
            if not os.path.exists(f):
                print("** Error: %s not found in %s" % (
                    f, self.get_main_folder()))
                return False
            else:
                return True

    def rm_file(self, filepath):
        """Remove file from document, it also removes the entry in `files`

        :filepath: Full file path for file
        """
        basename = os.path.basename(filepath)
        if basename not in self['files']:
            raise Exception("File %s not tracked by document" % basename)
        os.remove(filepath)
        self['files'].pop(self['files'].index(basename))

    def rm(self):
        """Removes document's folder, effectively removing it from the library.
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
                    confirmation = \
                        papis.utils.confirm(
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
        structure = yaml.load(fd)
        fd.close()
        for key in structure:
            self[key] = structure[key]
