import os
import yaml
import logging
import papis.utils
import papis.config
import papis.bibtex


class Document(object):

    """Structure implementing all information inside a document, which should
    be yaml information with few methods
    """

    def __init__(self, folder):
        self._keys = []
        self._folder = folder
        self.logger = logging.getLogger("Doc")
        self._infoFilePath = \
            os.path.join(folder, papis.utils.getInfoFileName())
        self.loadInformationFromFile()
        self.subfolder = self.getMainFolder()\
                             .replace(os.environ["HOME"], "")\
                             .replace("/", " ")

    def __delitem__(self, obj):
        """
        :obj: TODO
        :returns: TODO
        """
        self._keys.pop(self._keys.index(obj))
        delattr(self, obj)

    def __setitem__(self, obj, value):
        """
        :obj: TODO
        :returns: TODO
        """
        self._keys.append(obj)
        setattr(self, obj, value)

    def __getitem__(self, obj):
        return getattr(self, obj) if hasattr(self, obj) else ""

    def getMainFolder(self):
        """
        Get main folder where the document and the information is stored
        :returns: Folder path
        """
        return self._folder

    def getMainFolderName(self):
        """
        Get main folder name where the document and the information is stored
        :returns: Folder name
        """
        return os.path.basename(self._folder)

    def has(self, key):
        """Check if the information file has some key defined

        :key: Key name to be checked
        :returns: True/False

        """
        if key in self.keys():
            return True
        else:
            return False

    def checkFile(self):
        """
        :returns: TODO
        """
        # Check for the exsitence of the document
        for f in self.get_files():
            self.logger.debug(f)
            if not os.path.exists(f):
                print("** Error: %s not found in %s" % (
                    f, self.getMainFolder()))
                return False
            else:
                return True

    def save(self):
        """
        :returns: TODO
        """
        fd = open(self._infoFilePath, "w+")
        structure = dict()
        for key in self.keys():
            structure[key] = self[key]
        self.logger.debug("Saving %s " % self.getInfoFile())
        yaml.dump(structure, fd, default_flow_style=False)
        fd.close()

    def toDict(self):
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

    def toVcf(self):
        if not papis.config.inMode("contact"):
            self.logger.error("Not in contact mode")
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
                for t in self[contact_type].keys() if self[contact_type][t] is not None
            ])
        text += "\n"
        text += "END:VCARD"
        return text

    def toBibtex(self):
        """
        :f: TODO
        :returns: TODO
        """
        bibtexString = ""
        bibtexType = ""
        # First the type, article ....
        if "type" in self.keys():
            if self["type"] in papis.bibtex.bibtexTypes:
                bibtexType = self["type"]
        if not bibtexType:
            bibtexType = "article"
        if not self["ref"]:
            ref = os.path.basename(self.getMainFolder())
        else:
            ref = self["ref"]
        bibtexString += "@%s{%s,\n" % (bibtexType, ref)
        for bibKey in papis.bibtex.bibtexKeys:
            if bibKey in self.keys():
                bibtexString += "\t%s = { %s },\n" % (bibKey, self[bibKey])
        bibtexString += "}\n"
        return bibtexString

    def update(self, data, force=False, interactive=False):
        """TODO: Docstring for update.

        :data: TODO
        :force: TODO
        :interactive: TODO
        :returns: TODO

        """
        self.logger.debug("Updating...")
        for key in data:
            if self[key] != data[key]:
                if force:
                    self[key] = data[key]
                elif interactive:
                    confirmation = \
                        input("(%s conflict) Replace '%s' by '%s'? (y/N)" % (
                            key, self[key], data[key]
                            )) or "N"
                    if confirmation in "Yy":
                        self[key] = data[key]
                else:
                    pass

    def getInfoFile(self):
        """TODO: Docstring for get_files.
        :returns: TODO

        """
        return self._infoFilePath

    def get_files(self):
        """TODO: Docstring for get_files.
        :returns: TODO

        """
        files = self["files"] if isinstance(self["files"], list) \
            else [self["files"]]
        result = []
        for f in files:
            result.append(os.path.join(self.getMainFolder(), f))
        return result

    def keys(self):
        """TODO: Docstring for keys().

        :arg1: TODO
        :returns: TODO

        """
        return self._keys

    def dump(self):
        """TODO: Docstring for dump.
        :returns: TODO

        """
        string = ""
        for i in self.keys():
            string += str(i)+":   "+str(self[i])+"\n"
        return string

    def loadInformationFromFile(self):
        """
        load information from file
        :returns: TODO
        """
        try:
            fd = open(self._infoFilePath, "r")
        except:
            print("Warning: No info file found")
            return False
        structure = yaml.load(fd)
        fd.close()
        for key in structure:
            self[key] = structure[key]
