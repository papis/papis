from ..document import Document
import papis
import os
import shutil
import papis.utils
from . import Command


class Export(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        # export parser
        self.subparser = self.parser.add_parser(
            "export",
            help="""Export a document from a given library"""
        )
        self.subparser.add_argument(
            "document",
            help="Document search",
            nargs="?",
            default=".",
            action="store"
        )
        self.subparser.add_argument(
            "--bibtex",
            help="Export into bibtex",
            default=False,
            action="store_true"
        )
        self.subparser.add_argument(
            "--folder",
            help="Export document folder to share",
            default=False,
            action="store_true"
        )
        self.subparser.add_argument(
            "-o",
            "--out",
            help="Outfile or outdir",
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
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        folders = papis.utils.getFilteredFolders(documentsDir, documentSearch)
        folder = self.pick(folders, config, strip=documentsDir)
        self.logger.debug(folder)
        document = Document(folder)
        if args.bibtex:
            print(document.toBibtex())
        if args.folder:
            outdir = args.out or os.path.basename(folder)
            shutil.copytree(folder, outdir)
        else:
            print(document.dump())
