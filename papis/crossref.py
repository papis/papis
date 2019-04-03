import logging
import papis.config
import papis.utils
import papis.doi
import habanero
import re

logger = logging.getLogger("crossref")
logger.debug("importing")


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
            {k: a.get(k) for k in ['given', 'family']}
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
                logger.warning(
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


def get_data(query="", author="", title="", dois=[], max_results=0):
    assert(isinstance(dois, list))
    data = dict(
        query=query, query_author=author,
        ids=dois,
        query_title=title, limit=max_results
    )
    kwargs = {key: data[key] for key in data.keys() if data[key]}
    if not dois:
        kwargs.update(dict(sort='relevance'))
    try:
        results = _get_crossref_works(**kwargs)
    except Exception as e:
        logger.error(e)
        return []

    if isinstance(results, list):
        docs = [d["message"] for d in results]
    elif isinstance(results, dict):
        if 'message' not in results.keys():
            logger.error("Error retrieving from xref, I got an incorrect message")
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


def doi_to_data(doi):
    """Search through crossref and get a dictionary containing the data

    :param doi: Doi identificator or an url with some doi
    :type  doi: str
    :returns: Dictionary containing the data
    :raises ValueError: If no data could be retrieved for the doi

    """
    global logger
    assert(isinstance(doi, str))
    doi = papis.doi.get_clean_doi(doi)
    results = get_data(dois=[doi])
    if results:
        return results[0]
    else:
        raise ValueError(
            "Couldn't get data for doi ({doi})".format(doi=doi)
        )
