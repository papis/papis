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
import papis.document


def run(
    documents,
    yaml=False,
    bibtex=False,
    json=False,
    text=False
):
    """
    Exports several documents into something else.

    :param document: A ist of papis document
    :type  document: [papis.document.Document]
    :param yaml: Wether to return a yaml string
    :type  yaml: bool
    :param bibtex: Wether to return a bibtex string
    :type  bibtex: bool
    :param json: Wether to return a json string
    :type  json: bool
    :param text: Wether to return a text string representing the document
    :type  text: bool
    """
    if json:
        import json
        return json.dumps(
            [
                papis.document.to_dict(document) for document in documents
            ]
        )

    if yaml:
        import yaml
        return yaml.dump_all(
            [
                papis.document.to_dict(document) for document in documents
            ],
            allow_unicode=True
        )

    if bibtex:
        return '\n'.join([
            papis.document.to_bibtex(document) for document in documents
        ])

    if text:
        text_format = papis.config.get('export-text-format')
        return '\n'.join([
            papis.utils.format_doc(text_format, document)
            for document in documents
        ])

    return None


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
            "--file",
            help="Export (copy) pdf file to outfile",
            default=False,
            action="store_true"
        )

    def main(self):

        documents = self.get_db().query(self.args.search)

        if self.args.json and self.args.folder or \
           self.args.yaml and self.args.folder:
            self.logger.warning("Only --folder flag will be considered")

        if not self.args.all:
            document = self.pick(documents)
            if not document:
                return 0
            documents = [document]

        if self.args.out and not self.get_args().folder \
        and not self.args.file:
            self.args.out = open(self.get_args().out, 'a+')

        if not self.args.out and not self.get_args().folder \
        and not self.args.file:
            self.args.out = sys.stdout

        ret_string = run(
            documents,
            yaml=self.args.yaml,
            bibtex=self.args.bibtex,
            json=self.args.json,
            text=self.args.text
        )

        if ret_string is not None:
            self.args.out.write(ret_string)
            return 0

        for document in documents:
            if self.args.folder:
                folder = document.get_main_folder()
                outdir = self.args.out or document.get_main_folder_name()
                if not len(documents) == 1:
                    outdir = os.path.join(
                        outdir, document.get_main_folder_name()
                    )
                shutil.copytree(folder, outdir)
                if not self.args.no_bibtex:
                    open(
                        os.path.join(outdir, "info.bib"),
                        "a+"
                    ).write(papis.document.to_bibtex(document))
            elif self.args.file:
                files = document.get_files()
                if self.args.all:
                    files_to_open = files
                else:
                    files_to_open = [papis.api.pick(
                        files,
                        pick_config=dict(
                            header_filter=lambda x: x.replace(
                                document.get_main_folder(), ""
                            )
                        )
                    )]
                for file_to_open in filter(lambda x: x, files_to_open):
                    print(file_to_open)
                    shutil.copyfile(
                        file_to_open,
                        self.args.out or os.path.basename(file_to_open)
                    )
