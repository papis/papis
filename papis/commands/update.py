"""This command is to update the information of the documents.
Some examples of the usage are given below

Examples
^^^^^^^^

- Update a document automatically and interactively
  (searching by ``doi`` number in *crossref*, or in other sources...)

    .. code::

        papis update --auto -i "author : dyson"

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

import colorama
import urllib.error
import logging
import papis.utils
import papis.strings
import papis.bibtex
import papis.downloaders
import papis.document
import papis.database
import papis.isbnplus
import papis.isbn
import papis.crossref
import papis.base
import papis.pick
import papis.cli
import papis.yaml
import click


def update_document(document, data, force=False, interactive=False):
    """Update document's information from an info dictionary.

    :param data: Dictionary with key and values to be updated
    :type  data: dict
    :param force: If True, the update turns into a replace, i.e., it
        replaces the old value by the new value stored in data.
    :type  force: bool
    :param interactive: If True, it will ask for user's input every time
        that the values differ.
    :type  interactive: bool

    """
    logger = logging.getLogger('cli:update')
    _log = logger.info
    for key in data.keys():
        if document[key] == data[key]:
            continue
        if force:
            setkey = True
        else:
            if document[key] is None or document[key] == '':
                message = [
                    ('', 'Set "'),
                    ('bg:ansiblack fg:ansiyellow bold',
                        '{val}'.format(val=key)),
                    ('', '" to "'),
                    ('bg:ansiblack fg:green bold',
                        '{val:.200}'.format(val=str(data[key]))),
                    ('bg:ansiblack bold', '"? (Y/n) '),
                ]
                setkey = True
            else:
                message = [
                    ('bg:ansiblack fg:ansiyellow',
                        "({key} conflict)".format(key=key)),
                    ('bg:ansired', "\n"),
                    ('', 'Replace "'),
                    ('bg:ansiblack fg:ansired bold',
                        '{val:.200}'.format(val=str(document[key]))),
                    ('', '"\nby      "'),
                    ('bg:ansiblack fg:green bold',
                        '{val:.200}'.format(val=str(data[key]))),
                    ('bg:ansiblack bold', '"? (Y/n) '),
                ]
                setkey = False

            if interactive:
                setkey = papis.utils.confirm(message)
                _log = logger.debug

        if setkey:
            _log(
                'setting {key} to {value}'.format(key=key, value=data[key])
            )
            document[key] = data[key]
        else:
            _log(
                'NOT setting {key} to {value}'.format(key=key, value=data[key])
            )


def _update_with_database(document):
    document.save()
    papis.database.get().update(document)


def run(document, data=dict(), interactive=False, force=False):
    # Keep the ref the same, otherwise issues can be caused when
    # writing LaTeX documents and all the ref's change
    data['ref'] = document['ref']

    update_document(document, data, force, interactive)
    _update_with_database(document)


@click.command("update")
@click.help_option('--help', '-h')
@papis.cli.query_option()
@papis.cli.doc_folder_option()
@click.option(
    "-i/-b",
    "--interactive/--no-interactive",
    help="Interactive or batch mode",
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
@click.option(
    "-d", "--delete",
    help="Delete document's key",
    multiple=True,
    type=str,
)
@click.option(
    "--sort",
    "sort_field",
    help="Sort results by field",
    default=None
)
def cli(
        query,
        doc_folder,
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
        set,
        sort_field,
        delete
        ):
    """Update a document from a given library"""

    documents = papis.database.get().query(query, sort_field)
    logger = logging.getLogger('cli:update')
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)

    if doc_folder:
        documents = [papis.document.from_folder(doc_folder)]

    if not all:
        documents = filter(
            lambda d: d,
            [papis.pick.pick_doc(documents)]
        )

    for document in documents:
        data = dict()

        logger.info(
            'Updating '
            '{c.Back.WHITE}{c.Fore.BLACK}{0}{c.Style.RESET_ALL}'
            .format(papis.document.describe(document), c=colorama)
        )

        if set:
            data.update(
                {s[0]: papis.utils.format_doc(s[1], document) for s in set}
            )

        if delete:
            for key in delete:
                _delete_key = False
                _confirmation = True
                if interactive:
                    _confirmation = papis.utils.confirm(
                        "Delete {key}?".format(key=key))
                if interactive and _confirmation and not force:
                    _delete_key = True
                elif not _confirmation:
                    _delete_key = False
                else:
                    _delete_key = True
                if _delete_key:
                    try:
                        logger.warning('Deleting {key}'.format(key=key))
                        del document[key]
                    except ValueError:
                        logger.error('Document has no {key}'.format(key=key))
                    else:
                        _update_with_database(document)

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
            query = papis.utils.format_doc(from_crossref, document)
            logger.info('Trying with crossref with query {0}'.query(query))
            if from_crossref is True:
                from_crossref = ''
            try:
                doc = papis.pick.pick_doc([
                        papis.document.from_data(d)
                        for d in papis.crossref.get_data(
                            query=query,
                            author=document['author'],
                            title=document['title']
                        )
                ])
                if doc:
                    data.update(papis.document.to_dict(doc))
                    if 'doi' in document.keys() and not from_doi and auto:
                        from_doi = doc['doi']

            except Exception as e:
                logger.error('error processing crossref')
                logger.error(e)

        if from_base:
            query = papis.utils.format_doc(from_base, document)
            logger.info('Trying with base with query {0}'.format(query))
            try:
                doc = papis.pick.pick_doc([
                    papis.document.from_data(d)
                    for d in papis.base.get_data(query=query)
                ])
                if doc:
                    data.update(papis.document.to_dict(doc))
            except urllib.error.HTTPError:
                logger.error('urllib failed to download')

        if from_isbnplus:
            logger.info('Trying with isbnplus')
            logger.warning('Isbnplus support is does not work... Not my fault')

        if from_isbn:
            query = papis.utils.format_doc(from_isbn, document)
            logger.info('Trying with isbn ({0:20})'.format(query))
            try:
                doc = papis.pick.pick_doc([
                    papis.document.from_data(d)
                    for d in papis.isbn.get_data(query=query)
                ])
                if doc:
                    data.update(papis.document.to_dict(doc))
            except Exception as e:
                logger.error('Isbnlib had an error retrieving information')
                logger.error(e)

        if from_yaml:
            data.update(papis.yaml.yaml_to_data(from_yaml))

        if from_doi:
            query = papis.utils.format_doc(from_doi, document)
            logger.info("Try using doi %s" % query)
            doidata = papis.crossref.doi_to_data(query)
            if doidata:
                data.update(doidata)

        if from_bibtex:
            try:
                bib_data = papis.bibtex.bibtex_to_dict(from_bibtex)
                data.update(bib_data[0])
            except Exception as e:
                logger.error('error processing bibtex')
                logger.error(e)

        if from_url:
            query = papis.utils.format_doc(from_url, document)
            logger.info('Trying url {0}'.format(query))
            try:
                url_data = papis.downloaders.get_info_from_url(query)
                data.update(url_data["data"])
            except Exception as e:
                logger.error('error processing url')
                logger.error(e)

        run(
            document,
            data=data,
            interactive=interactive,
            force=force,
        )
