import papis
import os
import sys
import re
import yaml
import tempfile
import vobject
import hashlib
import shutil
import string
import subprocess
import papis.utils
import papis.config
import papis.bibtex
import papis.document
import papis.downloaders.utils

class Add(papis.commands.Command):

    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "add",
            help="Add a document into a given library"
        )

        self.parser.add_argument(
            "document",
            help="Document file name",
            default=[],
            nargs="*",
            action="store"
        )

        self.parser.add_argument(
            "-d", "--dir",
            help="Subfolder in the library",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--name",
            help="Name for the main folder",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--edit",
            help="Edit info file after adding document",
            action="store_true"
        )

        self.parser.add_argument(
            "--title",
            help="Title for document",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--author",
            help="Author(s) for document",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--from-bibtex",
            help="Parse information from a bibtex file",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--from-yaml",
            help="Parse information from a yaml file",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--from-url",
            help="""Get document and information from a
                    given url, a parser must be
                    implemented""",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--from-doi",
            help="Doi to try to get information from",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--from-vcf",
            help="""\
                Get contact information from a vcard (.vcf)
                file""",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--to",
            help="""When --to is specified, the document will be added to the
            selected already existing document entry.""",
            nargs="?",
            action="store"
        )

        self.parser.add_argument(
            "--confirm",
            help="Ask to confirm before adding to the collection",
            action="store_true"
        )

        self.parser.add_argument(
            "--commit",
            help="Commit document if library is a git repository",
            action="store_true"
        )

    def get_hash_folder(self, data, document_path):
        """Folder name where the document will be stored.

        :data: Data parsed for the actual document
        :document_path: Path of the document

        """
        author = "-{:.20}".format(data["author"])\
                 if "author" in data.keys() else ""
        fd = open(document_path, "rb")
        md5 = hashlib.md5(fd.read(4096)).hexdigest()
        fd.close()
        result = re.sub(r"[\\'\",.(){}]", "", md5 + author)\
                   .replace(" ", "-")
        return result

    def get_document_extension(self, documentPath):
        """Get document extension

        :document_path: Path of the document
        :returns: Extension (string)

        """
        m = re.match(r"^(.*)\.([a-zA-Z0-9]*)$", os.path.basename(documentPath))
        extension = m.group(2) if m else "txt"
        self.logger.debug("[ext] = %s" % extension)
        return extension

    def get_meta_data(self, key, document_path):
        self.logger.debug("Retrieving %s meta data" % key)
        extension = self.get_document_extension(document_path)
        if "pdf" in extension:
            # We put the import statements here because they slow down the
            # whole program if initializing the cli command it is in the top,
            # only import it if it is being used
            import pdfminer.pdfparser
            import pdfminer.pdfdocument
            fd = open(document_path, "rb")
            parsed = pdfminer.pdfparser.PDFParser(fd)
            doc = pdfminer.pdfdocument.PDFDocument(parsed)
            fd.close()
            for info in doc.info:
                for info_key in info.keys():
                    if info_key.lower() == key.lower():
                        self.logger.debug(
                            "Found %s meta data %s" %
                            (info_key, info[info_key])
                        )
                        return info[info_key].decode("utf-8")
        elif "epub" in extension:
            if key == "author":
                key = "Creator"
            info = papis.utils.get_epub_info(document_path)
            for info_key in info.keys():
                if info_key.lower() == key.lower():
                    self.logger.debug(
                        "Found %s meta data %s" %
                        (info_key, info[info_key])
                    )
                    return str(info[info_key])
        return None

    def get_default_title(self, data, document_path):
        if "title" in data.keys():
            return data["title"]
        extension = self.get_document_extension(document_path)
        title = self.get_meta_data("title", document_path)
        if not title:
            title = os.path.basename(document_path)\
                            .replace("."+extension, "")\
                            .replace("_", " ")\
                            .replace("-", " ")
        return title

    def get_default_author(self, data, document_path):
        if "author" in data.keys():
            return data["author"]
        author = self.get_meta_data("author", document_path)
        if not author:
            author = "Unknown"
        return author

    def clean_document_name(self, documentPath):
        base = os.path.basename(documentPath)
        self.logger.debug("Cleaning document name %s " % base)
        return re.sub(r"[^a-zA-Z0-9_.-]", "",
                      re.sub(r"\s+", "-", base)
                      )

    def init_contact_mode(self):
        """Initialize the contact mode
        """
        self.logger.debug("Initialising contact mode")
        self.args.document = [papis.utils.get_info_file_name()]
        self.args.from_yaml = papis.utils.get_info_file_name()
        if os.path.exists(self.args.document[0]):
            return True
        self.args.edit = True
        self.args.confirm = True
        template = papis.document.Document.get_vcf_template()
        fd = open(self.args.document[0], "w+")
        fd.write(template)
        fd.close()

    def vcf_to_data(self, vcard_path):
        data = yaml.load(papis.document.Document.get_vcf_template())
        self.logger.debug("Reading in %s " % vcard_path)
        text = open(vcard_path).read()
        vcard = vobject.readOne(text)
        try:
            data["first_name"] = vcard.n.value.given
            self.logger.debug("First name = %s" % data["first_name"])
        except:
            data["first_name"] = None
        try:
            data["last_name"] = vcard.n.value.family
            self.logger.debug("Last name = %s" % data["last_name"])
        except:
            data["last_name"] = None
        try:
            if not isinstance(vcard.org.value[0], list):
                data["org"] = vcard.org.value
            else:
                data["org"] = vcard.org.value
            self.logger.debug("Org = %s" % data["org"])
        except:
            data["org"] = []
        for ctype in ["tel", "email"]:
            try:
                vcard_asset = getattr(vcard, ctype)
                self.logger.debug("Parsing %s" % ctype)
            except:
                pass
            else:
                try:
                    param_type = getattr(vcard_asset, "type_param")
                except:
                    param_type = "home"
                data[ctype][param_type.lower()] = getattr(vcard_asset, "value")
        self.logger.debug("Read in data = %s" % data)
        return data

    def main(self):
        if papis.config.inMode("contact"):
            self.init_contact_mode()
        documentsDir = os.path.expanduser(self.get_config()[self.args.lib]["dir"])
        folderName = None
        data = dict()
        self.logger.debug("Saving in directory %s" % documentsDir)
        # if documents are posible to download from url, overwrite
        documents_paths = self.args.document
        documents_names = []
        temp_dir = tempfile.mkdtemp("-"+self.args.lib)
        if self.args.from_url:
            url_data = papis.downloaders.utils.get(self.args.from_url)
            data.update(url_data["data"])
            documents_paths.extend(url_data["documents_paths"])
        if self.args.from_bibtex:
            data.update(papis.bibtex.bibtex_to_dict(self.args.from_bibtex))
        if self.args.from_doi:
            self.logger.debug("Try using doi %s" % self.args.from_doi)
            data.update(papis.utils.doi_to_data(self.args.from_doi))
        if self.args.from_yaml:
            data.update(yaml.load(open(self.args.from_yaml)))
        if self.args.from_vcf:
            data.update(self.vcf_to_data(self.args.from_vcf))
        documents_names = [
            self.clean_document_name(documentPath)
            for documentPath in documents_paths
        ]
        if self.args.to:
            documents = papis.utils.get_documents_in_dir(
                documentsDir,
                self.args.to
            )
            document = self.pick(documents)
            if not document:
                sys.exit(0)
            data = document.to_dict()
            documents_paths = [
                os.path.join(
                    document.get_main_folder(),
                    d
                ) for d in document["files"]] + documents_paths
            data["files"] = document["files"] + documents_names
            folderName = document.get_main_folder_name()
            fullDirPath = document.get_main_folder()
        else:
            document = papis.document.Document(temp_dir)
            print(document["org"])
            if not papis.config.inMode("contact"):
                data["title"] = self.args.title or self.get_default_title(
                    data,
                    documents_paths[0]
                )
                data["author"] = self.args.author or self.get_default_author(
                    data,
                    documents_paths[0]
                )
                self.logger.debug("Author = % s" % data["author"])
                self.logger.debug("Title = % s" % data["title"])
            if not self.args.name:
                folderName = self.get_hash_folder(data, documents_paths[0])
            else:
                folderName = string\
                            .Template(self.args.name)\
                            .safe_substitute(data)\
                            .replace(" ", "-")
            data["files"] = documents_names
            fullDirPath = os.path.join(
                documentsDir, self.args.dir,  folderName
            )
        ######
        self.logger.debug("Folder = % s" % folderName)
        self.logger.debug("File = % s" % documents_paths)
        ######
        if not os.path.isdir(temp_dir):
            self.logger.debug("Creating directory '%s'" % temp_dir)
            os.makedirs(temp_dir)
        if self.args.edit:
            document.update(data, force=True)
            document.save()
            papis.utils.edit_file(document.get_info_file())
            document.load()
            data = document.to_dict()
        for i in range(min(len(documents_paths), len(data["files"]))):
            documentName = data["files"][i]
            documentPath = documents_paths[i]
            assert(os.path.exists(documentPath))
            endDocumentPath = os.path.join(
                    document.get_main_folder(), documentName)
            if os.path.exists(endDocumentPath):
                self.logger.debug(
                    "%s exists, ignoring..." % endDocumentPath
                )
                continue
            self.logger.debug(
                "[CP] '%s' to '%s'" %
                (documentPath, endDocumentPath)
            )
            shutil.copy(documentPath, endDocumentPath)
        document.update(data, force=True)
        if self.args.confirm:
            if input("Really add? (Y/n): ") in ["N", "n"]:
                sys.exit(0)
        document.save()
        if self.args.to:
            sys.exit(0)
        self.logger.debug(
            "[MV] '%s' to '%s'" %
            (document.get_main_folder(), fullDirPath)
        )
        shutil.move(document.get_main_folder(), fullDirPath)
        papis.utils.clear_lib_cache(self.args.lib)
        if self.args.commit and papis.utils.lib_is_git_repo(self.args.lib):
            subprocess.call(["git", "-C", fullDirPath, "add", "."])
            subprocess.call(
                ["git", "-C", fullDirPath, "commit", "-m", "\"Add document\""]
            )
