import papis
import os
import sys
import re
import tempfile
import hashlib
import shutil
import string
import subprocess
import papis.utils
import papis.config
import papis.bibtex
import papis.document
import papis.downloaders.utils

class Command(papis.commands.Command):

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
            default=None,
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
            action='store_false' if papis.config.get('add-confirm') \
                else 'store_true'
        )

        self.parser.add_argument(
            "--open",
            help="Open file before adding document",
            action='store_false' if papis.config.get('add-open') \
                else 'store_true'
        )

        self.parser.add_argument(
            "--edit",
            help="Edit info file before adding document",
            action='store_false' if papis.config.get('add-edit') \
                else 'store_true'
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
                        try:
                            # Sometimes there is a problem with decoding
                            # utf8 because of pdfminer implementation
                            return info[info_key].decode("utf-8")
                        except:
                            return None
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


    def main(self):
        if papis.config.in_mode("contact"):
            self.init_contact_mode()
        lib_dir = os.path.expanduser(papis.config.get('dir'))
        folderName = None
        data = dict()
        in_documents_paths = self.args.document
        documents_names = []
        temp_dir = tempfile.mkdtemp("-"+self.args.lib)
        if self.args.from_url:
            url_data = papis.downloaders.utils.get(self.args.from_url)
            data.update(url_data["data"])
            in_documents_paths.extend(url_data["documents_paths"])
            # If no data was retrieved and doi was found, try to get
            # information with the document's doi
            if not data and\
                url_data["doi"] is not None and\
                not self.args.from_doi:
                self.args.from_doi = url_data["doi"]
        if self.args.from_bibtex:
            data.update(papis.bibtex.bibtex_to_dict(self.args.from_bibtex))
        if self.args.from_doi:
            self.logger.debug("Try using doi %s" % self.args.from_doi)
            data.update(papis.utils.doi_to_data(self.args.from_doi))
            if len(self.get_args().document) == 0 and \
                    papis.config.get('doc-url-key-name') in data.keys():
                doc_url = data[papis.config.get('doc-url-key-name')]
                self.logger.info(
                    'I am trying to download the document from %s' % doc_url
                )
                down = papis.downloaders.utils.get_downloader(
                    doc_url,
                    'get'
                )
                file_name = tempfile.mktemp()
                fd = open(file_name, 'wb+')
                fd.write(down.getDocumentData())
                fd.close()
                self.logger.info('Opening the file')
                papis.utils.open_file(file_name)
                if papis.utils.confirm('Do you want to use this file?'):
                    self.args.document.append(file_name)

        if self.args.from_yaml:
            data.update(papis.utils.yaml_to_data(self.args.from_yaml))
        if self.args.from_vcf:
            data.update(papis.utils.vcf_to_data(self.args.from_vcf))
        documents_names = [
            self.clean_document_name(documentPath)
            for documentPath in in_documents_paths
        ]
        if self.args.to:
            documents = papis.utils.get_documents_in_dir(
                lib_dir,
                self.args.to
            )
            document = self.pick(documents)
            if not document:
                sys.exit(0)
            data = document.to_dict()
            in_documents_paths = [
                os.path.join(
                    document.get_main_folder(),
                    d
                ) for d in document["files"]] + in_documents_paths
            data["files"] = document["files"] + documents_names
            folderName = document.get_main_folder_name()
            fullDirPath = document.get_main_folder()
        else:
            document = papis.document.Document(temp_dir)
            print(document["org"])
            if not papis.config.in_mode("contact"):
                data["title"] = self.args.title or self.get_default_title(
                    data,
                    in_documents_paths[0]
                )
                data["author"] = self.args.author or self.get_default_author(
                    data,
                    in_documents_paths[0]
                )
                self.logger.debug("Author = % s" % data["author"])
                self.logger.debug("Title = % s" % data["title"])
            if not self.args.name:
                folderName = self.get_hash_folder(data, in_documents_paths[0])
            else:
                folderName = string\
                            .Template(self.args.name)\
                            .safe_substitute(data)\
                            .replace(" ", "-")
            data["files"] = documents_names
            fullDirPath = os.path.join(
                lib_dir, self.args.dir,  folderName
            )
        ######
        self.logger.debug("Folder = % s" % folderName)
        self.logger.debug("File = % s" % in_documents_paths)
        ######
        if not os.path.isdir(temp_dir):
            self.logger.debug("Creating directory '%s'" % temp_dir)
            os.makedirs(temp_dir)
        if self.args.edit:
            document.update(data, force=True)
            document.save()
            papis.utils.edit_file(document.get_info_file())
            self.logger.debug("Loading the changes made by editing")
            document.load()
            data = document.to_dict()
        for i in range(min(len(in_documents_paths), len(data["files"]))):
            documentName = data["files"][i]
            documentPath = in_documents_paths[i]
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
        if self.get_args().open:
            for d_path in in_documents_paths:
                papis.utils.open_file(d_path)
        if self.args.confirm:
            if not papis.utils.confirm('Really add?'):
                sys.exit(0)
        document.save()
        if self.args.to:
            sys.exit(0)
        self.logger.debug(
            "[MV] '%s' to '%s'" %
            (document.get_main_folder(), fullDirPath)
        )
        shutil.move(document.get_main_folder(), fullDirPath)
        papis.utils.clear_lib_cache()
        if self.args.commit and papis.utils.lib_is_git_repo(self.args.lib):
            subprocess.call(["git", "-C", fullDirPath, "add", "."])
            subprocess.call(
                ["git", "-C", fullDirPath, "commit", "-m", "\"Add document\""]
            )
