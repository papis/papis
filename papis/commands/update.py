"""This command is to update the information of the documents.
Some examples of the usage are given below

Examples
^^^^^^^^

- Update a document automatically and interactively
(searching by ``doi`` number in *crossref*, or in other sources...)

    .. code::

        papis update --auto -i "author = dyson"

- Update your library from a bib(la)tex file where many entries are listed.
  papis will try to look for documents in your library that match these
  entries and will ask you entry per entry to update it (of course this is
  done if you use the ``-i`` flag for interactively doing it). In the example
  ``libraryfile.bib`` is a file containing many entries.

    .. code::

        papis update --from-bibtex libraryfile.bib -i

"""
import papis
import os
import sys
import shutil
import papis.utils
import papis.bibtex
import papis.downloaders.utils
import papis.api
import papis.document


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "update",
            help="Update a document from a given library"
        )

        self.add_search_argument()

        self.parser.add_argument(
            "-i",
            "--interactive",
            help="Interactively update",
            default=False,
            action="store_true"
        )

        self.parser.add_argument(
            "-f",
            "--force",
            help="Force update, overwrite conflicting information",
            default=False,
            action="store_true"
        )

        self.parser.add_argument(
            "-d",
            "--document",
            help="Overwrite an existing document",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--from-isbnplus",
            help="Update info from isbnplus.org",
            action="store"
        )

        self.parser.add_argument(
            "--from-yaml",
            help="Update info from yaml file",
            action="store"
        )

        self.parser.add_argument(
            "--from-bibtex",
            help="Update info from bibtex file",
            action="store"
        )

        self.parser.add_argument(
            "--from-url",
            help="Get document or information from url",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--from-doi",
            help="Doi to try to get information from",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--auto",
            help="Try to parse information from different sources",
            action="store_true"
        )

    def main(self):
        # TODO: Try to recycle some of this code with command add.
        import papis.api
        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
        )
        data = dict()

        if self.args.from_bibtex:
            bib_data = papis.bibtex.bibtex_to_dict(self.args.from_bibtex)
            # Then it means that the user wants to update all the information
            # appearing in the bibtex file
            if len(bib_data) > 1:
                self.logger.warning(
                    'Your bibtex file contains more than one entry,'
                )
                self.logger.warning(
                    'It is supposed that you want to update all the'
                    'documents appearing inside the bibtex file.'
                )
                for bib_element in bib_data:
                    doc = papis.document.Document(data=bib_element)
                    located_doc = papis.utils.locate_document(doc, documents)
                    if located_doc is None:
                        self.logger.error(
                            "The following information could not be located"
                        )
                        self.logger.error('\n'+doc.dump())
                    else:
                        located_doc.update(
                            bib_element,
                            self.args.force,
                            self.args.interactive
                        )
                        located_doc.save()
                return 0
            data.update(bib_data[0])

        if self.args.from_yaml:
            import yaml
            data.update(yaml.load(open(self.args.from_yaml)))

        # For the coming parts we need to pick a document
        document = self.pick(documents)
        if not document: return 0

        if self.args.auto:
            if 'doi' in document.keys() and not self.args.from_doi:
                self.args.from_doi = document['doi']
            if 'title' in document.keys() and not self.args.from_isbnplus:
                self.args.from_isbnplus = document['title']

        if self.args.from_isbnplus:
            import papis.isbn
            doc = self.pick(
                [
                    papis.document.Document(data=d)
                    for d in papis.isbn.get_data(
                        query=self.args.from_isbnplus
                    )
                ]
            )
            if doc:
                data.update(doc.to_dict())

        if self.args.from_url:
            url_data = papis.downloaders.utils.get(self.args.from_url)
            data.update(url_data["data"])
            document_paths = url_data["documents_paths"]
            if not len(document_paths) == 0:
                document_path = document_paths[0]
                old_doc = self.pick(document["files"])
                if papis.utils.confirm("Really replace document %s?" % old_doc):
                    new_path = os.path.join(
                        document.get_main_folder(), old_doc
                    )
                    self.logger.debug(
                        "Moving %s to %s" %(document_path, new_path)
                    )
                    shutil.move(document_path, new_path)

        if self.args.from_doi:
            self.logger.debug("Try using doi %s" % self.args.from_doi)
            data.update(papis.utils.doi_to_data(self.args.from_doi))

        document.update(data, self.args.force, self.args.interactive)
        document.save()
