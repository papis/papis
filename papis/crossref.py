import logging
import papis.config
import papis.utils
import doi
import habanero
import re
import os
import click
import papis.document
import papis.importer
import papis.downloaders.base
import tempfile

logger = logging.getLogger("crossref")
logger.debug("importing")


_filter_names = set([
    "has_funder", "funder", "location", "prefix", "member", "from_index_date",
    "until_index_date", "from_deposit_date", "until_deposit_date",
    "from_update_date", "until_update_date", "from_created_date",
    "until_created_date", "from_pub_date", "until_pub_date",
    "from_online_pub_date", "until_online_pub_date", "from_print_pub_date",
    "until_print_pub_date", "from_posted_date", "until_posted_date",
    "from_accepted_date", "until_accepted_date", "has_license",
    "license_url", "license_version", "license_delay",
    "has_full_text", "full_text_version", "full_text_type",
    "full_text_application", "has_references", "has_archive",
    "archive", "has_orcid", "has_authenticated_orcid",
    "orcid", "issn", "type", "directory", "doi", "updates", "is_update",
    "has_update_policy", "container_title", "category_name", "type",
    "type_name", "award_number", "award_funder", "has_assertion",
    "assertion_group", "assertion", "has_affiliation", "alternative_id",
    "article_number", "has_abstract", "has_clinical_trial_number",
    "content_domain", "has_content_domain", "has_crossmark_restriction",
    "has_relation", "relation_type", "relation_object", "relation_object_type",
    "public_references", "publisher_name", "affiliation",
])

_types_values = [
    "book-section", "monograph", "report", "peer-review", "book-track",
    "journal-article", "book-part", "other", "book", "journal-volume",
    "book-set", "reference-entry", "proceedings-article", "journal",
    "component", "book-chapter", "proceedings-series", "report-series",
    "proceedings", "standard", "reference-book", "posted-content",
    "journal-issue", "dissertation", "dataset", "book-series", "edited-book",
    "standard-series",
]

_sort_values = [
"relevance", "score", "updated", "deposited", "indexed", "published",
"published-print", "published-online", "issued", "is-referenced-by-count",
"references-count",
]


_order_values = ['asc', 'desc']


type_converter = {
    "book": "book",
    "book-chapter": "inbook",
    "book-part": "inbook",
    "book-section": "inbook",
    "book-series": "incollection",
    "book-set": "incollection",
    "book-track": "inbook",
    "dataset": "misc",
    "dissertation": "phdthesis",
    "edited-book": "book",
    "journal-article": "article",
    "journal-issue": "misc",
    "journal-volume": "article",
    "monograph": "monograph",
    "other": "misc",
    "peer-review": "article",
    "posted-content": "misc",
    "proceedings-article": "inproceedings",
    "proceedings": "inproceedings",
    "proceedings-series": "inproceedings",
    "reference-book": "book",
    "report": "report",
    "report-series": "inproceedings",
    "standard-series": "incollection",
    "standard": "techreport",
}


key_conversion = {
    "DOI": {"key": "doi"},
    "URL": {"key": "url"},
    "author": {
        "key": "author_list",
        "action": lambda authors: [
            {k: a.get(k) for k in ['given', 'family', 'affiliation']}
            for a in authors
        ],
    },
    "container-title": {"key": "journal", "action": lambda x: x[0]},
    "issue": {},
    # "issued": {"key": "",},
    "language": {},
    "ISBN": {"key": "isbn"},
    "page": {
        "key": "pages",
        "action": lambda p: re.sub(r"(-[^-])", r"-\1", p),
    },
    "link": {
        "key": papis.config.get('doc-url-key-name'),
        "action": lambda x: x[1]["URL"]
    },
    "published-print": [
        {"key": "year", "action": lambda x: x.get("date-parts")[0][0]},
        {"key": "month", "action": lambda x: x.get("date-parts")[0][1]}
    ],
    "publisher": {},
    "reference": {
        "key": "citations",
        "action": lambda cs: [
            {key.lower(): c[key]
                for key in set(c.keys()) - set(("key", "doi-asserted-by"))}
            for c in cs
        ]
    },
    # "short-title": { "key": "", },
    # "subtitle": { "key": "", },
    "title": {"action": lambda t: " ".join(t)},
    "type": {"action": lambda t: type_converter[t]},
    "volume": {},
    "event": [  # Conferences
        {"key": "venue", "action": lambda x: x["location"]},
        {"key": "booktitle", "action": lambda x: x["name"]},
        {"key": "year", "action": lambda x: x['start']["date-parts"][0][0]},
        {"key": "month", "action": lambda x: x['start']["date-parts"][0][1]},
    ],
}


def crossref_data_to_papis_data(data):
    new_data = dict()

    for xrefkey in key_conversion.keys():
        if xrefkey not in data.keys():
            continue
        _conv_data_src = key_conversion[xrefkey]
        # _conv_data_src can be a dict or a list of dicts
        if isinstance(_conv_data_src, dict):
            _conv_data_src = [_conv_data_src]
        for _conv_data in _conv_data_src:
            papis_key = xrefkey
            papis_val = data[xrefkey]
            if 'key' in _conv_data.keys():
                papis_key = _conv_data['key']
            try:
                if 'action' in _conv_data.keys():
                    papis_val = _conv_data['action'](data[xrefkey])
                new_data[papis_key] = papis_val
            except Exception as e:
                logger.debug(
                    "Error while trying to parse {0} ({1})".format(
                        papis_key, e))

    if 'author_list' in new_data.keys():
        new_data['author'] = (
            papis.config.get('multiple-authors-separator')
            .join([
                papis.config.get("multiple-authors-format").format(au=author)
                for author in new_data['author_list']
            ])
        )

    new_data['ref'] = re.sub(r'\s', '', papis.utils.format_doc(
        papis.config.get("ref-format"), new_data
    ))

    return new_data


def _get_crossref_works(**kwargs):
    cr = habanero.Crossref()
    return cr.works(**kwargs)


def get_data(query="", author="", title="", dois=[], max_results=0,
        filters={}, sort="score", order='desc'):
    global _filter_names
    global _sort_values
    assert(isinstance(dois, list)), 'dois must be a list'
    assert(sort in _sort_values), 'Sort value not valid'
    assert(order in _order_values), 'Sort value not valid'
    assert(isinstance(filters, dict)), 'filters must be a dictionary'
    if filters:
        if not set(filters.keys()) & _filter_names == set(filters.keys()):
            raise Exception(
                'Filter keys must be one of {0}'
                .format(','.join(_filter_names))
            )
    data = dict(
        query=query, query_author=author,
        ids=dois,
        query_title=title, limit=max_results
    )
    kwargs = {key: data[key] for key in data.keys() if data[key]}
    if not dois:
        kwargs.update(dict(sort=sort, order=order))
    try:
        results = _get_crossref_works(filter=filters, **kwargs)
    except Exception as e:
        logger.error(e)
        return []

    if isinstance(results, list):
        docs = [d["message"] for d in results]
    elif isinstance(results, dict):
        if 'message' not in results.keys():
            logger.error(
                "Error retrieving from xref, I got an incorrect message")
            return []
        message = results['message']
        if "items" in message.keys():
            docs = message['items']
        else:
            docs = [message]
    else:
        logger.error("Error retrieving from xref, I got an incorrect message")
        return []
    logger.debug("Retrieved {} documents".format(len(docs)))
    return [
        crossref_data_to_papis_data(d)
        for d in docs
    ]


def doi_to_data(doi_string):
    """Search through crossref and get a dictionary containing the data

    :param doi_string: Doi identificator or an url with some doi
    :type  doi_string: str
    :returns: Dictionary containing the data
    :raises ValueError: If no data could be retrieved for the doi

    """
    global logger
    assert(isinstance(doi_string, str))
    doi_string = doi.get_clean_doi(doi_string)
    results = get_data(dois=[doi_string])
    if results:
        return results[0]
    else:
        raise ValueError(
            "Couldn't get data for doi ({doi})".format(doi=doi_string)
        )


@click.command('crossref')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--query', '-q', help='General query', default=None)
@click.option('--author', '-a', help='Author of the query', default=None)
@click.option('--title', '-t', help='Title of the query', default=None)
@click.option('--max', '-m', help='Maximum number of results', default=20)
@click.option(
    '--filter', '-f', help='Filters to apply', default=(),
    type=(click.Choice(_filter_names), str),
    multiple=True
)
@click.option(
    '--order', '-o', help='Order of appearance according to sorting',
    default='desc', type=click.Choice(_order_values), show_default=True
)
@click.option(
    '--sort', '-s', help='Sorting parameter', default='score',
    type=click.Choice(_sort_values), show_default=True
)
def explorer(ctx, query, author, title, max, filter, sort, order):
    """
    Look for documents on crossref.org.

    Examples of its usage are

    papis explore crossref -a 'Albert einstein' pick export --bibtex lib.bib

    """
    logger = logging.getLogger('explore:crossref')
    logger.info('Looking up...')
    data = get_data(
        query=query,
        author=author,
        title=title,
        max_results=max,
        filters=dict(filter),
        sort=sort,
        order=order
    )
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))


class DoiFromPdfImporter(papis.importer.Importer):

    """Importer parsing a doi from a pdf file"""

    def __init__(self, **kwargs):
        papis.importer.Importer.__init__(self, name='pdf2doi', **kwargs)
        self.doi = None

    @classmethod
    def match(cls, uri):
        if (os.path.isdir(uri) or not os.path.exists(uri) or
                not papis.utils.get_document_extension(uri) == 'pdf'):
            return None
        importer = DoiFromPdfImporter(uri=uri)
        importer.doi = doi.pdf_to_doi(uri, maxlines=2000)
        return importer if importer.doi else None

    def fetch(self):
        self.logger.info("Trying to parse doi from file {0}".format(self.uri))
        if not self.doi:
            self.doi = doi.pdf_to_doi(self.uri, maxlines=2000)
        if self.doi:
            self.logger.info("Parsed doi {0}".format(self.doi))
            self.logger.warning(
                "There is no guarantee that this doi is the one")
            importer = Importer(uri=self.doi)
            importer.fetch()
            self.ctx = importer.ctx


class Importer(papis.importer.Importer):

    """Importer getting files and data form a doi through crossref.org"""

    def __init__(self, **kwargs):
        papis.importer.Importer.__init__(
            self,
            name='doi', **kwargs)

    @classmethod
    def match(cls, uri):
        try:
            doi.validate_doi(uri)
        except ValueError:
            return None
        else:
            return Importer(uri=uri)

    def fetch(self):
        self.logger.info("using doi {0}".format(self.uri))
        doidata = papis.crossref.get_data(dois=[self.uri])
        if doidata:
            self.ctx.data = doidata[0]
            if papis.config.get('doc-url-key-name') in self.ctx.data.keys():
                doc_url = self.ctx.data[papis.config.get('doc-url-key-name')]
                self.logger.info(
                    'trying to download document from {0}..'
                    .format(doc_url))
                document_data = papis.utils.geturl(doc_url)
                tmp_filepath = tempfile.mktemp()
                self.logger.debug("Saving in %s" % tmp_filepath)
                with open(tmp_filepath, 'wb+') as fd:
                    fd.write(document_data)
                self.ctx.files.append(tmp_filepath)


class FromCrossrefImporter(papis.importer.Importer):

    """Importer that gets data from querying to crossref"""

    def __init__(self, **kwargs):
        papis.importer.Importer.__init__(self, name='crossref', **kwargs)

    @classmethod
    def match(cls, uri):
        # There is no way to check if it matches
        return None

    def fetch(self):
        self.logger.info("querying '{0}' to crossref.org".format(self.uri))
        docs = [
            papis.document.from_data(d)
            for d in get_data(query=self.uri)
        ]
        if docs:
            self.logger.info("got {0} matches, picking...".format(len(docs)))
            doc = papis.pick.pick_doc(docs)
            if doc:
                importer = Importer(uri=doc['doi'])
                importer.fetch()
                self.ctx = importer.ctx


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, uri):
        papis.downloaders.base.Downloader.__init__(self, uri=uri, name="doi")

    @classmethod
    def match(cls, uri):
        if doi.find_doi_in_text(uri):
            return Downloader(uri)
        else:
            return None

    def fetch(self):
        importer = Importer(uri=doi.find_doi_in_text(self.uri))
        importer.fetch()
        self.ctx = importer.ctx
