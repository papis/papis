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
            nargs="?",
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

    def main(self, config, args):
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        folderName = None
        data = dict()
        self.logger.debug("Saving in directory %s" % documentsDir)
        # if documents are posible to download from url, overwrite
        documentPath = args.document
        if args.from_url:
            self.logger.debug("Attempting to retrieve from url")
            url = args.from_url
            downloader = papis.downloaders.utils.getDownloader(url)
            if downloader:
                data = papis.bibtex.bibtexToDict(downloader.getBibtexData())
                if len(args.document) == 0:
                    doc_data = downloader.getDocumentData()
                    if doc_data:
                        documentPath = tempfile.mktemp()
                        self.logger.debug("Saving in %s" % documentPath)
                        tempfd = open(documentPath, "wb+")
                        tempfd.write(doc_data)
                        tempfd.close()
        elif args.from_bibtex:
            data = papis.bibtex.bibtexToDict(args.from_bibtex)
        else:
            pass
        extension = self.get_document_extension(documentPath)
        documentName = "document."+extension
        data["file"] = documentName
        if args.title:
            data["title"] = args.title
        if args.author:
            data["author"] = args.author
        if "title" not in data.keys():
            data["title"] = os.path.basename(documentPath)\
                            .replace("."+extension, "")
        if not args.name:
            folderName = self.get_hash_folder(data, documentPath)
        else:
            folderName = string\
                        .Template(args.name)\
                        .safe_substitute(data)\
                        .replace(" ", "-")
        endDocumentPath = os.path.join(
            documentsDir,
            args.dir,
            folderName,
            documentName
        )
        fullDirPath = os.path.join(documentsDir, args.dir,  folderName)
        ######
        self.logger.debug("Folder    = % s" % folderName)
        self.logger.debug("File      = % s" % documentPath)
        self.logger.debug("EndFile   = % s" % endDocumentPath)
        self.logger.debug("Ext.      = % s" % extension)
        ######
        if not os.path.isdir(fullDirPath):
            self.logger.debug("Creating directory '%s'" % fullDirPath)
            os.mkdir(fullDirPath)
        shutil.copy(documentPath, endDocumentPath)
        document = Document(fullDirPath)
        document.update(data, force=True)
        document.save()
