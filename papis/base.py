"""
TODO: Create an own python package for this

For description refer to
https://www.base-search.net/about/download/base_interface.pdf

"""
import urllib.parse
import urllib.request  # import urlencode
import papis.config
import logging
import json

logger = logging.getLogger('base')

BASE_BASEURL = "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi/"

def get_data(query="", max=20):

    logger.warning('BASE engine in papis is experimental')

    if max > 125:
        logger.error('BASE only allows a maximum of 125 hits')
        max = 125

    results = []
    dict_params = {
        "func": "PerformSearch",
        "query": query,
        "format": "json",
        "hits": max,
    }
    params = urllib.parse.urlencode(
        {x: dict_params[x] for x in dict_params if dict_params[x]}
    )
    req_url = BASE_BASEURL + "search?" + params
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


def basedoc_to_papisdoc(basedoc):
    """Convert a json doc from the base database into a papis document

    :basedoc: Json doc from base database
    :returns: Dictionary containing its data

    """
    doc = dict()
    keys_translate = [
        ("dctitle", "title", "single"),
        ("dcyear", "year", "single"),
        ("dclink", "url", "single"),
        ("dcdescription", "abstract", "single"),
        ("dcpublisher", "publisher", "multi", lambda x: x[0]),
        ("dcperson", "author", "multi", lambda x: " and ".join(x)),
        ("dcsubject", "tags", "multi", lambda x: " ".join(x)),
        ("dcdoi", "doi", "multi", lambda x: x[0]),
        ("dctype", "type", "multi", lambda x: x[0].lower()),
        ("dclang", "lang", "mutli", lambda x: x[0]),
    ]
    for kt in keys_translate:
        if kt[0] in basedoc.keys():
            key = kt[1]
            if kt[2] == "multi":
                value = basedoc[kt[0]]
                value = kt[3](value) if kt[3] is not None else value
            else:
                value = basedoc[kt[0]]
            doc[key] = value
    return doc
