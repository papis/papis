import papis
import os
import sys
import shutil
import papis.utils


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "export",
            help="""Export a document from a given library"""
        )

        self.add_search_argument()

        self.parser.add_argument(
            "--yaml",
            help="Export into bibtex",
            default=False,
            action="store_true"
        )

        self.parser.add_argument(
            "--bibtex",
            help="Export into bibtex",
            default=False,
            action="store_true"
        )

        self.parser.add_argument(
            "--folder",
            help="Export document folder to share",
            default=False,
            action="store_true"
        )

        self.parser.add_argument(
            "--no-bibtex",
            help="When exporting to a folder, do not include the bibtex",
            default=False,
            action="store_true"
        )

        self.parser.add_argument(
            "-o",
            "--out",
            help="Outfile or outdir",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "-t",
            "--text",
            help="Text formated reference",
            action="store_true"
        )

        self.parser.add_argument(
            "-a", "--all",
            help="Export all without picking",
            action="store_true"
        )

        self.parser.add_argument(
            "--vcf",
            help="Export contact to vcf format",
            action="store_true"
        )

    def export(self, document):
        """Main action in export command
        """
        folder = document.get_main_folder()
        if not self.args.folder and not self.args.out:
            self.args.out = "/dev/stdout"
        if self.args.bibtex:
            print(document.to_bibtex())
        if self.args.text:
            text_format = papis.config.get('export-text-format')
            text = papis.utils.format_doc(text_format, document)
            open(self.args.out, "w").write(text)
        elif self.args.folder:
            outdir = self.args.out or document.get_main_folder_name()
            shutil.copytree(folder, outdir)
            if not self.args.no_bibtex:
                open(
                    os.path.join(outdir, "info.bib"),
                    "w+"
                ).write(document.to_bibtex())
        elif self.args.yaml:
            open(self.args.out, "w").write(document.dump())
        elif self.args.vcf:
            open(self.args.out, "w").write(document.to_vcf())
        else:
            pass

    def main(self):

        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
        )

        if not self.args.all:
            document = self.pick(documents) or sys.exit(0)
            documents = [document]

        for document in documents:
            self.export(document)
