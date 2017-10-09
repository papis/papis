import os
import sys
import shutil
import papis.utils
import papis.config
import papis.bibtex


class Document(object):

    """Class implementing the entry abstraction of a document in a library.
    It is basically a python dictionary with more methods.
    """

    subfolder = ""
    _infoFilePath = ""

    def __init__(self, folder=None, data=None):
        self._keys = []
        self._folder = folder
        if folder is not None:
            self._infoFilePath = \
                os.path.join(folder, papis.utils.get_info_file_name())
            self.load()
            self.subfolder = self.get_main_folder()\
                                 .replace(os.environ["HOME"], "")\
                                 .replace("/", " ")
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
        yaml.dump(structure, fd, default_flow_style=False)
        fd.close()

    def to_json(self):
        """Export information into a json string
        :returns: Json formatted info file
        :rtype:  str
        """
        import json
        return json.dumps(self.to_dict())

    def to_dict(self):
        """Gets a python dictionary with the information of the document
        :returns: Python dictionary
        :rtype:  dict
        """
        result = dict()
        for key in self.keys():
            result[key] = self[key]
        return result

    @classmethod
    def get_vcf_template(cls):
        return """\
first_name: null
last_name: null
org:
- null
email:
    work: null
    home: null
tel:
    cell: null
    work: null
    home: null
adress:
    work: null
    home: null"""

    def to_vcf(self):
        # TODO: Generalize using the doc variable.
        if not papis.config.in_mode("contact"):
            # self.logger.error("Not in contact mode")
            sys.exit(1)
        text = \
            """\
BEGIN:VCARD
VERSION:4.0
FN:{doc[first_name]} {doc[last_name]}
N:{doc[last_name]};{doc[first_name]};;;""".format(doc=self)
        for contact_type in ["email", "tel"]:
            text += "\n"
            text += "\n".join([
                "{contact_type};TYPE={type}:{tel}"\
                .format(
                    contact_type=contact_type.upper(),
                    type=t.upper(),
                    tel=self[contact_type][t]
                    )
                for t in self[contact_type].keys() \
                if self[contact_type][t] is not None
            ])
        text += "\n"
        text += "END:VCARD"
        return text

    def to_bibtex(self):
        """Create a bibtex string from document's information
        :returns: String containing bibtex formating
        :rtype:  str
        """
        bibtexString = ""
        bibtexType = ""
        # First the type, article ....
        if "type" in self.keys():
            if self["type"] in papis.bibtex.bibtex_types:
                bibtexType = self["type"]
        if not bibtexType:
            bibtexType = "article"
        if not self["ref"]:
            ref = os.path.basename(self.get_main_folder())
        else:
            ref = self["ref"]
        bibtexString += "@%s{%s,\n" % (bibtexType, ref)
        for bibKey in papis.bibtex.bibtex_keys:
            if bibKey in self.keys():
                bibtexString += "\t%s = { %s },\n" % (bibKey, self[bibKey])
        bibtexString += "}\n"
        return bibtexString

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

    def dump(self):
        """Return information string without any obvious format
        :returns: String with document's information
        :rtype:  str

        """
        string = ""
        for i in self.keys():
            string += str(i)+":   "+str(self[i])+"\n"
        return string

    def load(self):
        """Load information from info file
        """
        import yaml
        # TODO: think about if it's better to raise an exception here
        # TODO: if no info file is found
        try:
            fd = open(self._infoFilePath, "r")
        except:
            return False
        structure = yaml.load(fd)
        fd.close()
        for key in structure:
            self[key] = structure[key]
