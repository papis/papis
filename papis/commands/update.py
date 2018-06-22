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
import urllib.error
import logging
import papis.utils
import papis.bibtex
import papis.downloaders.utils
import papis.document
import papis.database
import papis.isbn
import papis.api

def run(
    document,
    data=dict(),
    interactive=False,
    force=False,
    from_yaml=False,
    from_bibtex=False,
    from_url=False,
    from_doi=False,
    args=False
        ):
    logger = logging.getLogger('update:run')

    if from_yaml:
        import yaml
        data.update(yaml.load(open(from_yaml)))

    elif from_bibtex:
        try:
            bib_data = papis.bibtex.bibtex_to_dict(from_bibtex)
            data.update(bib_data[0])
        except Exception:
            pass
        
    elif from_url:
        try:
            url_data = papis.downloaders.utils.get(from_url)
            data.update(url_data["data"])
        except Exception:
            pass
            
    elif from_doi:
        logger.debug("Try using doi %s" % from_doi)
        data.update(papis.utils.doi_to_data(from_doi))

    document.update(data, force, interactive)
    document.save()
    papis.database.get().update(document)
    # if not args.all:
    #     return 0


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
            default=None,
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

        self.parser.add_argument(
            "--all",
            help="Update all entries in library",
            action="store_true"
        )

    def main(self):
        # TODO: Try to recycle some of this code with command add.
        documents = self.get_db().query(self.args.search)
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
                        self.logger.error('\n'+papis.document.dump(doc))
                    else:
                        run(
                            located_doc,
                            data=bib_element,
                            force=self.args.force,
                            interactive=self.args.interactive
                        )
                return 0

        # For the coming parts we need to pick a document
        if not self.args.all:
            document = [self.pick(documents)]
            if not document:
                return 0
        else:
            document = documents

        for docs in document:
            if self.args.all:
                data = dict()
                self.args.from_url = None
                self.args.from_doi = None
                self.args.from_isbnplus = None
            if self.args.auto:
                if 'doi' in docs.keys() and not self.args.from_doi:
                    self.args.from_doi = docs['doi']
                elif 'url' in docs.keys() and not self.args.from_url:
                    self.args.from_url = docs['url']
                elif 'title' in docs.keys() and not self.args.from_isbnplus:
                    self.args.from_isbnplus = docs['title']

                    
            if self.args.from_isbnplus:
                try:
                    doc = self.pick(
                        [
                            papis.docs.Document(data=d)
                            for d in papis.isbn.get_data(
                                query=self.args.from_isbnplus
                            )
                        ]
                    )
                    if doc:
                        data.update(doc.to_dict())
                except urllib.error.HTTPError:
                    self.logger.error('urllib failed to download')

            run(
                docs,
                data=data,
                interactive=self.args.interactive,
                force=self.args.force,
                from_yaml=self.args.from_yaml,
                from_bibtex=self.args.from_bibtex,
                from_url=self.args.from_url,
                from_doi=self.args.from_doi,
                args = self.args
            )

            # papis.api.clear_lib_cache()
