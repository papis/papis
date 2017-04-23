from ..document import Document
import papis
import os
import re
import tempfile
import hashlib
import shutil
import string
import papis.utils
import papis.bibtex
from . import Command
import papis.downloaders.utils
import pdfminer.pdfparser
import pdfminer.pdfdocument


class Add(Command):

    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        self.subparser = self.parser.add_parser(
            "add",
            help="Add a document into a given library"
        )
        self.subparser.add_argument(
            "document",
            help="Document file name",
            default="",
            nargs="*",
            action="store"
        )
        self.subparser.add_argument(
            "-d", "--dir",
            help="Subfolder in the library",
            default="",
            action="store"
        )
        self.subparser.add_argument(
            "--name",
            help="Name for the main folder",
            default="",
            action="store"
        )
        self.subparser.add_argument(
            "--edit",
            help="Edit info file after adding document",
            default="",
            action="store_true"
        )
        self.subparser.add_argument(
            "--from-bibtex",
            help="Parse information from a bibtex file",
            default="",
            action="store"
        )
        self.subparser.add_argument(
            "--title",
            help="Title for document",
            default="",
            action="store"
        )
        self.subparser.add_argument(
            "--author",
            help="Author(s) for document",
            default="",
            action="store"
        )
        self.subparser.add_argument(
            "--from-url",
            help="""Get document and information from a
                    given url, a parser must be
                    implemented""",
            default="",
            action="store"
        )
        self.subparser.add_argument(
            "--to",
            help="""When --to is specified, the document will be added to the
            selected already existing document entry.""",
            nargs="?",
            action="store"
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
        extension = m.group(2) if m else "pdf"
        self.logger.debug("[ext] = %s" % extension)
        return extension

    def get_meta_data(self, key, document_path):
        self.logger.debug("Retrieving %s meta data" % key)
        extension = self.get_document_extension(document_path)
        if "pdf" in extension:
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
        return False

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
        return re.sub(r"[^a-zA-Z0-9_.-]", "",
           re.sub(r"\s+", "-",
               os.path.basename(documentPath)
            )
        )

    def main(self, config, args):
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        folderName = None
        data = dict()
        self.logger.debug("Saving in directory %s" % documentsDir)
        # if documents are posible to download from url, overwrite
        documents_paths = args.document
        documents_names = []
        if args.from_url:
            self.logger.debug("Attempting to retrieve from url")
            url = args.from_url
            downloader = papis.downloaders.utils.getDownloader(url)
            if downloader:
                data = papis.bibtex.bibtexToDict(downloader.getBibtexData())
                if len(args.document) == 0:
                    doc_data = downloader.getDocumentData()
                    if doc_data:
                        documents_paths.append(tempfile.mktemp())
                        self.logger.debug("Saving in %s" % documents_paths[-1])
                        tempfd = open(documents_paths[-1], "wb+")
                        tempfd.write(doc_data)
                        tempfd.close()
        elif args.from_bibtex:
            data = papis.bibtex.bibtexToDict(args.from_bibtex)
        else:
            pass
        documents_names = [
            self.clean_document_name(documentPath)
            for documentPath in documents_paths
        ]
        if args.title:
            data["title"] = args.title
        else:
            data["title"] = self.get_default_title(data, documents_paths[0])
        if args.author:
            data["author"] = args.author
        else:
            data["author"] = self.get_default_author(data, documents_paths[0])
        if not args.name:
            folderName = self.get_hash_folder(data, documents_paths[0])
        else:
            folderName = string\
                        .Template(args.name)\
                        .safe_substitute(data)\
                        .replace(" ", "-")
        if args.to:
            documents = papis.utils.getFilteredDocuments(
                documentsDir,
                args.to
            )
            document = self.pick(documents, config)
            data["file"] = document["file"] + documents_names
            if not document:
                sys.exit(0)
            folderName = os.path.basename(document.getMainFolder())
        else:
            data["file"] = documents_names
        fullDirPath = os.path.join(documentsDir, args.dir,  folderName)
        ######
        self.logger.debug("Folder    = % s" % folderName)
        self.logger.debug("File      = % s" % documents_paths)
        self.logger.debug("Author    = % s" % data["author"])
        self.logger.debug("Title    = % s" % data["title"])
        ######
        if not os.path.isdir(fullDirPath):
            self.logger.debug("Creating directory '%s'" % fullDirPath)
            os.makedirs(fullDirPath)
        for i in range(len(documents_paths)):
            documentName = documents_names[i]
            documentPath = documents_paths[i]
            endDocumentPath = os.path.join(fullDirPath, documentName)
            self.logger.debug(
                "[CP] '%s' to '%s'" %
                (documentPath, fullDirPath)
            )
            shutil.copy(documentPath, endDocumentPath)
        document = Document(fullDirPath)
        document.update(data, force=True)
        document.save()
        if args.edit:
            papis.utils.editFile(document.getInfoFile(), config)
