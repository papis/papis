try:
    import logging
    logger = logging.getLogger('papis:ads')
    import ads
except ImportError:
    logger.warning(
        'You need the package ads, try "pip3 install ads"'
    )

fields = [
    "abstract",
    "ack",
    "aff",
    "arxiv_class",
    "author",
    "bibgroup",
    "bibstem",
    "body",
    "citation_count",
    "database",
    "doi",
    "first_author",
    "identifier",
    "issue",
    "keyword",
    "lang",
    "page",
    "read_count",
    "title",
    "volume",
    "year",
    "sort",
]

ads.config.token = 'pBZxhQUlTV8NDX2kbfqCFOb8pZpjx3DHwhhjTyR0'

def paper_to_dict(paper):
    #keys = paper.keys()
    data = paper._raw
    if isinstance(paper.author, list):
        data['author'] = ' and '.join(paper.author)
    if isinstance(paper.title, list):
        data['title'] = paper.title[0]
    # if isinstance(paper.doi, list):
        # data['doi'] = paper.doi
    # else:
        # del data['doi']
    return data


def get_data(
        query=None,
        max_results=30,
        **kwargs
        ):
    """
    :param abstract: The abstract of the record
    :param ack: The acknowledgements section of an article
    :param aff: An array of the authors' affiliations
    :param arxiv_class: The arXiv class the pre-print was submitted to
    :param author: An array of the author names associated with the record
    :param bibgroup: The bibliographic groups that the bibcode has been
        associated with
    :param bibstem: The abbreviated name of the journal or publication, e.g.,
        ApJ.
    :param body: The full text content of the article
    :param citation_count: Number of citations the item has received
    :param database: Database the record is associated with (astronomy,
        physics, or general). By default, all three databases are searched; to
        limit to astronomy articles, add fq=database:astronomy to the URL
    :param doi: Digital object identifier of the article
    :param first_author: The first author of the article
    :param identifier: An array of alternative identifiers for the record. May
        contain alternate bibcodes, DOIs and/or arxiv ids.
    :param issue: Issue the record appeared in
    :param keyword: An array of normalized and un-normalized keyword values
        associated with the record
    :param lang: The language of the article's title
    :param page: Starting page
    :param read_count: Number of times the record has been viewed within in a
        90-day windows (ads and arxiv)
    :param title: The title of the record
    :param volume: Volume the record appeared in
    :param year: The year the article was published
    :param sort: Any of the fields
    """
    query_dict = {k: kwargs[k] for k in kwargs if kwargs[k]}
    query_dict['q'] = 'ein'
    papers = ads.SearchQuery(
        rows=max_results,
        query_dict=query_dict
    )
    return [paper_to_dict(p) for p in papers]
