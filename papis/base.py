"""
TODO: Create an own python package for this

For description refer to
https://www.base-search.net/about/download/base_interface.pdf

"""

from typing import Optional, Dict, Any, List, Callable, NamedTuple

import click

import papis.utils
import papis.logging

logger = papis.logging.get_logger(__name__)

# NOTE: the BASE API is documented at
#   https://www.base-search.net/about/download/base_interface.pdf
BASE_API_URL = "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi/"

BASE_MAX_HITS = 120
BASE_MAX_QUERY_LENGTH = 1000


def get_data(
        query: str = "",
        hits: int = 10,
        boost: bool = False) -> List[Dict[str, Any]]:
    """
    :param query: a query string to pass to the BASE search API
        (maximum 1000 characters).
    :param hits: maximum number of returned results
        (maximum 120).
    :param boost: push open access documents upwards in the results.
    """
    logger.warning("BASE engine in papis is experimental!")

    if hits > BASE_MAX_HITS:
        logger.error("BASE only allows a maximum of %d hits (got %d hits).",
                     BASE_MAX_HITS, hits)
        hits = BASE_MAX_HITS

    if len(query) > BASE_MAX_QUERY_LENGTH:
        logger.error("BASE only allows queries of maximum %d characters (got %d).",
                     BASE_MAX_QUERY_LENGTH, len(query))
        query = query[:BASE_MAX_QUERY_LENGTH]

    with papis.utils.get_session() as session:
        response = session.get(
            BASE_API_URL,
            params={
                "func": "PerformSearch",
                "query": query if query else None,
                "format": "json",
                "hits": str(hits),
                "boost": "oa" if boost else None,
            })

    if not response.ok:
        logger.error("An HTTP error (%d %s) was encountered for query: '%s'.",
                     response.status_code, response.reason, query)
        return []

    jsondoc = response.json()
    if "response" not in jsondoc:
        logger.error("Error querying BASE API: '%s'.", jsondoc["error"])
        return []

    docs = jsondoc["response"]["docs"]

    logger.info("Retrieved %d documents.", len(docs))
    return [basedoc_to_papisdoc(doc) for doc in docs]


def basedoc_to_papisdoc(basedoc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a json doc from the base database into a papis document

    :basedoc: Json doc from base database
    :returns: Dictionary containing its data

    """
    doc = {}
    _action_type = Optional[Callable[[List[str]], str]]
    _key_translate = NamedTuple("_key_translate", [("basekey", str),
                                                   ("papiskey", str),
                                                   ("mode", str),
                                                   ("action", _action_type)
                                                   ])
    keys_translate = [
        _key_translate("dctitle", "title", "s", None),
        _key_translate("dcyear", "year", "s", None),
        _key_translate("dclink", "url", "s", None),
        _key_translate("dcdescription", "abstract", "s", None),
        _key_translate("dcpublisher", "publisher", "m", lambda x: x[0]),
        _key_translate("dcperson", "author", "m", lambda x: " and ".join(x)),
        _key_translate("dcsubject", "tags", "m", lambda x: " ".join(x)),
        _key_translate("dcdoi", "doi", "m", lambda x: x[0]),
        _key_translate("dctype", "type", "m", lambda x: x[0].lower()),
        _key_translate("dclang", "lang", "m", lambda x: x[0]),
    ]  # type: List[_key_translate]

    for kt in keys_translate:
        if kt.basekey not in basedoc:
            continue
        key = kt.papiskey
        if kt.mode == "m":
            value = basedoc[kt.basekey]
            value = kt.action(value) if kt.action is not None else value
        else:
            value = basedoc[kt.basekey]
        doc[key] = value
    return doc


@click.command("base")
@click.pass_context
@click.help_option("--help", "-h")
@click.option("--query", "-q", default=None)
def explorer(ctx: click.core.Context, query: str) -> None:
    """
    Look for documents on the BielefeldAcademicSearchEngine

    Examples of its usage are

    papis explore base -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    import papis.document
    logger.info("Looking up...")

    data = get_data(query=query)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("%d documents found", len(docs))
