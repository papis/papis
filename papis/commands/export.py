"""
The export command is useful to work with other programs such as bibtex.

Some examples of its usage are:

    - Export one of the documents matching the author with einstein to bibtex:

    .. code::

        papis export --bibtex 'author = einstein'

    or export all of them

    .. code::

        papis export --bibtex --all 'author = einstein'

    - Export all documents to bibtex and save them into a ``lib.bib`` file

    .. code::

        papis export --all --bibtex --out lib.bib

    - Export a folder of one of the documents matching the word ``krebs``
      into a folder named, ``interesting-document``

    .. code::

        papis export --folder --out interesting-document krebs

    this will create the folder ``interesting-document`` containing the
    ``info.yaml`` file, the linked documents and a ``bibtex`` file for
    sharing with other people.

"""
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
            help="Export into yaml",
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
            "--json",
            help="Export into json",
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

    def main(self):

        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
        )

        if not self.args.all:
            document = self.pick(documents)
            if not document: return 0
            documents = [document]

        if self.args.out and not self.get_args().folder:
            self.args.out = open(self.get_args().out, 'a+')

        if not self.args.out and not self.get_args().folder:
            self.args.out = sys.stdout

        if self.args.json:
            import json
            return self.args.out.write(
                json.dumps([document.to_dict() for document in documents])
            )

        if self.args.yaml:
            import yaml
            return self.args.out.write(
                yaml.dump_all([document.to_dict() for document in documents])
            )

        for document in documents:
            if self.args.bibtex:
                self.args.out.write(document.to_bibtex())
            if self.args.text:
                text_format = papis.config.get('export-text-format')
                text = papis.utils.format_doc(text_format, document)
                self.args.out.write(text)
            elif self.args.folder:
                folder = document.get_main_folder()
                outdir = self.args.out or document.get_main_folder_name()
                if not len(documents) == 1:
                    outdir = os.path.join(
                        outdir, document.get_main_folder_name())
                shutil.copytree(folder, outdir)
                if not self.args.no_bibtex:
                    open(
                        os.path.join(outdir, "info.bib"),
                        "a+"
                    ).write(document.to_bibtex())
            elif self.args.vcf:
                self.args.out.write(document.to_vcf())
            else:
                pass
