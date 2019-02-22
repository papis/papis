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

- Tag all einstein papers with the tag classics

    .. code::

        papis update --all --set tags classics einstein

and add the tag of ``physics`` to all papers tagged as ``classics``

    .. code::

        papis update --all --set tags '{doc[tags]} physics' einstein

Cli
^^^
.. click:: papis.commands.update:cli
    :prog: papis update
"""

import papis
import urllib.error
import logging
import papis.utils
import papis.bibtex
import papis.downloaders.utils
import papis.document
import papis.database
import papis.isbnplus
import papis.isbn
import papis.crossref
import papis.base
import papis.api
import papis.cli
import click
import yaml


def run(document, data=dict(), interactive=False, force=False):
    # Keep the ref the same, otherwise issues can be caused when
    # writing LaTeX documents and all the ref's change
    data['ref'] = document['ref']

    document.update(data, force, interactive)
    document.save()
    papis.database.get().update(document)


@click.command("update")
@click.help_option('--help', '-h')
@papis.cli.query_option()
@click.option(
    "-i/-b",
    "--interactive/--no-interactive",
    help="Interactively update",
    default=True
)
@click.option(
    "-f",
    "--force",
    help="Force update, overwrite conflicting information",
    default=False,
    is_flag=True
)
@click.option(
    "--from-crossref",
    help="Update info from crossref.org",
    default=None
)
@click.option(
    "--from-isbn",
    help="Update info from isbn",
    default=None
)
@click.option(
    "--from-isbnplus",
    help="Update info from isbnplus.org",
    default=None
)
@click.option(
    "--from-base",
    help="Update info from Bielefeld Academic Search Engine",
    default=None
)
@click.option(
    "--from-yaml",
    help="Update info from yaml file",
    default=None
)
@click.option(
    "--from-bibtex",
    help="Update info from bibtex file",
    default=None
)
@click.option(
    "--from-url",
    help="Get document or information from url",
    default=None
)
@click.option(
    "--from-doi",
    help="Doi to try to get information from",
    default=None
)
@click.option(
    "--auto",
    help="Try to parse information from different sources",
    default=False,
    is_flag=True
)
@click.option(
    "--all",
    help="Update all entries in library",
    default=False,
    is_flag=True
)
@click.option(
    "-s", "--set",
    help="Update document's information with key value."
         "The value can be a papis format.",
    multiple=True,
    type=(str, str),
)
def cli(
        query,
        interactive,
        force,
        from_crossref,
        from_base,
        from_isbnplus,
        from_isbn,
        from_yaml,
        from_bibtex,
        from_url,
        from_doi,
        auto,
        all,
        set
        ):
    """Update a document from a given library"""

    documents = papis.database.get().query(query)
    data = dict()
    logger = logging.getLogger('cli:update')

    if not all:
        documents = [papis.api.pick_doc(documents)]

    for document in documents:
        if all:
            data = dict()
            from_url = None
            from_doi = None
            from_isbnplus = None
            from_isbnplus = None

        if set:
            data.update(
                {s[0]: papis.utils.format_doc(s[1], document) for s in set}
            )

        if auto:
            if 'doi' in document.keys() and not from_doi:
                logger.info('Trying using the doi {}'.format(document['doi']))
                from_doi = document['doi']
            if 'url' in document.keys() and not from_url:
                logger.info('Trying using the url {}'.format(document['url']))
                from_url = document['url']
            if 'title' in document.keys() and not from_isbn:
                from_isbn = '{d[title]} {d[author]}'.format(d=document)
                from_isbnplus = from_isbn
                from_base = from_isbn
                logger.info(
                    'Trying with `from_isbn`, `from_isbnplus` and `from_base` '
                    'with the text "{0}"'.format(from_isbn)
                )
            if from_crossref is None and from_doi is None:
                from_crossref = True

        if from_crossref:
            logger.info('Trying with crossref')
            if from_crossref is True:
                from_crossref = ''
            try:
                doc = papis.api.pick_doc([
                        papis.document.from_data(d)
                        for d in papis.crossref.get_data(
                            query=from_crossref,
                            author=document['author'],
                            title=document['title']
                        )
                ])
                if doc:
                    data.update(papis.document.to_dict(doc))
                    if 'doi' in document.keys() and not from_doi and auto:
                        from_doi = doc['doi']

            except Exception as e:
                logger.error(e)

        if from_base:
            logger.info('Trying with base')
            try:
                doc = papis.api.pick_doc(
                    [
                        papis.document.from_data(d)
                        for d in papis.base.get_data(
                            query=from_isbnplus
                        )
                    ]
                )
                if doc:
                    data.update(papis.document.to_dict(doc))
            except urllib.error.HTTPError:
                logger.error('urllib failed to download')

        if from_isbnplus:
            logger.info('Trying with isbnplus')
            logger.warning('Isbnplus does not work... Not my fault')
            # try:
                # doc = papis.api.pick_doc(
                    # [
                        # papis.document.from_data(d)
                        # for d in papis.isbnplus.get_data(
                            # query=from_isbnplus
                        # )
                    # ]
                # )
                # if doc:
                    # data.update(papis.document.to_dict(doc))
            # except urllib.error.HTTPError:
                # logger.error('urllib failed to download')

        if from_isbn:
            logger.info('Trying with isbn')
            try:
                doc = papis.api.pick_doc(
                    [
                        papis.document.from_data(d)
                        for d in papis.isbn.get_data(
                            query=from_isbn
                        )
                    ]
                )
                if doc:
                    data.update(papis.document.to_dict(doc))
            except Exception as e:
                logger.error('Isbnlib had an error retrieving information')
                logger.error(e)

        if from_yaml:
            with open(from_yaml) as fd:
                data.update(yaml.load(fd))

        if from_doi:
            logger.debug("Try using doi %s" % from_doi)
            data.update(papis.utils.doi_to_data(from_doi))

        if from_bibtex:
            try:
                bib_data = papis.bibtex.bibtex_to_dict(from_bibtex)
                data.update(bib_data[0])
            except Exception:
                pass

        if from_url:
            logger.info('Trying url {0}'.format(from_url))
            try:
                url_data = papis.downloaders.utils.get(from_url)
                data.update(url_data["data"])
            except Exception:
                pass

        run(
            document,
            data=data,
            interactive=interactive,
            force=force,
        )
