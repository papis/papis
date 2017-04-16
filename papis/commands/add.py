from ..document import Document
import papis
import os
import re
import tempfile
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
            help="Document search",
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
            "--from-url",
            help="""Get document and information from a
                    given url, a parser must be
                    implemented""",
            default="",
            action="store"
        )

    def main(self, config, args):
        """
        Main action if the command is triggered

        :config: User configuration
        :args: CLI user arguments
        :returns: TODO

        """
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        folderName = None
        data = dict()
        self.logger.debug("Using directory %s" % documentsDir)
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
        m = re.match(r"^(.*)\.([a-zA-Z]*)$", os.path.basename(documentPath))
        extension = m.group(2) if m else "pdf"
        self.logger.debug("[ext] = %s" % extension)
        # Set foldername
        if not args.from_bibtex and not args.name and not args.from_url:
            folderName = m.group(1) if m else os.path.basename(documentPath)
        elif (args.from_bibtex or args.from_url) and not args.name:
            args.name = '$year-$author-$title'
        if folderName is None:
            folderName = folderName if not args.name else \
                                        string\
                                        .Template(args.name)\
                                        .safe_substitute(data)\
                                        .replace(" ", "-")
        documentName = "document."+extension
        endDocumentPath = os.path.join(documentsDir,
                                       args.dir,
                                       folderName,
                                       documentName)
        fullDirPath = os.path.join(documentsDir, args.dir,  folderName)
        ######
        data["file"] = documentName
        self.logger.debug("Folder    = % s" % folderName)
        self.logger.debug("File      = % s" % documentPath)
        self.logger.debug("EndFile   = % s" % endDocumentPath)
        self.logger.debug("Ext.      = % s" % extension)
        if not os.path.isdir(fullDirPath):
            self.logger.debug("Creating directory '%s'" % fullDirPath)
            os.mkdir(fullDirPath)
        shutil.copy(documentPath, endDocumentPath)
        document = Document(fullDirPath)
        document.update(data, force=True)
        document.save()
