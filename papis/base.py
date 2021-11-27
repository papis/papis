"""
TODO: Create an own python package for this

For description refer to
https://www.base-search.net/about/download/base_interface.pdf

"""
import urllib.parse
import urllib.request  # import urlencode
import logging
import json
from typing import Optional, Dict, Any, List, Callable, NamedTuple

import click

logger = logging.getLogger('base')


def get_data(query: str = "", max: int = 20) -> List[Dict[str, Any]]:
    base_baseurl = (
        "https://api.base-search.net/"
        "cgi-bin/BaseHttpSearchInterface.fcgi/"
    )

    logger.warning('BASE engine in papis is experimental')

    if max > 125:
        logger.error('BASE only allows a maximum of 125 hits')
        max = 125

    dict_params = {
        "func": "PerformSearch",
        "query": query,
        "format": "json",
        "hits": max,
    }
    params = urllib.parse.urlencode(
        {x: dict_params[x] for x in dict_params if dict_params[x]}
    )
    req_url = base_baseurl + "search?" + params
    logger.debug("url = " + req_url)
    url = urllib.request.Request(
        req_url,
        headers={
            'User-Agent': 'papis'
        }
    )
    jsondoc = json.loads(urllib.request.urlopen(url).read().decode())
    docs = jsondoc.get('response').get('docs')
    logger.info("Retrieved {0} documents".format(len(docs)))
    return list(map(basedoc_to_papisdoc, docs))


def basedoc_to_papisdoc(basedoc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a json doc from the base database into a papis document

    :basedoc: Json doc from base database
    :returns: Dictionary containing its data

    """
    doc = dict()
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
        _key_translate("dclang", "lang", "mutli", lambda x: x[0]),
    ]  # type: List[_key_translate]
    for kt in keys_translate:
        if kt.basekey not in basedoc.keys():
            continue
        key = kt.papiskey
        if kt.mode == "m":
            value = basedoc[kt.basekey]
            value = kt.action(value) if kt.action is not None else value
        else:
            value = basedoc[kt.basekey]
        doc[key] = value
    return doc


@click.command('base')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--query', '-q', default=None)
def explorer(ctx: click.core.Context, query: str) -> None:
    """
    Look for documents on the BielefeldAcademicSearchEngine

    Examples of its usage are

    papis explore base -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    import papis.document
    logger = logging.getLogger('explore:base')
    logger.info('Looking up...')
    data = get_data(query=query)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))
