import papis
import os
import shutil
import string
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
            "--yaml",
            help="Export into bibtex",
            default=False,
            action="store_true"
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
            "--no-bibtex",
            help="When exporting to a folder, do not include the bibtex",
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

        self.subparser.add_argument(
            "-t",
            "--text",
            help="Text formated reference",
            action="store_true"
        )

        self.subparser.add_argument(
            "--vcf",
            help="Export contact to vcf format",
            action="store_true"
        )


    def main(self, args):
        """
        Main action if the command is triggered

        :config: User configuration
        :args: CLI user arguments
        :returns: TODO

        """
        documentsDir = os.path.expanduser(self.config[self.args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = self.args.document
        documents = papis.utils.getFilteredDocuments(
            documentsDir,
            documentSearch
        )
        document = self.pick(documents)
        folder = document.getMainFolder()
        if self.args.bibtex:
            print(document.toBibtex())
        if self.args.text:
            text = string.Template(
                """$author. $title. $journal $pages $month $year"""
                ).safe_substitute(
                    document.toDict()
                )
            print(text)
        elif self.args.folder:
            outdir = self.args.out or document.getMainFolderName()
            shutil.copytree(folder, outdir)
            if not self.args.no_bibtex:
                open(
                    os.path.join(outdir, "info.bib"),
                    "w+"
                ).write(document.toBibtex())
        elif self.args.yaml:
            print(document.dump())
        elif self.args.vcf:
            print(document.toVcf())
        else:
            pass
