import logging
import urllib.request  # urlopen, Request
import urllib.parse  # import urlencode
import papis.config
import json


logger = logging.getLogger('dissemin')


def dissemin_authors_to_papis_authors(data):
    new_data = dict()
    if 'authors' in data.keys():
        authors = []
        for author in data['authors']:
            keys = ('first', 'last')
            authors.append(
                dict(
                    given_name=author['name']['first'],
                    surname=author['name']['last']
                )
            )
        new_data["author_list"] = authors
        new_data["author"] = ",".join(
            ["{a[given_name]} {a[surname]}".format(a=a) for a in authors]
        )
    return new_data


def dissemindoc_to_papis(data):
    common_data = dict()
    result = []
    common_data['title'] = data.get('title')
    common_data['type'] = data.get('type')
    common_data.update(dissemin_authors_to_papis_authors(data))
    for record in data['records']:
        new_data = dict()
        new_data.update(common_data)
        new_data.update(record)
        new_data['doc_url'] = new_data.get('pdf_url')
        new_data['url'] = new_data.get('splash_url')
        new_data['tags'] = new_data.get('keywords')

        new_data = {key: new_data[key] for key in new_data if new_data[key]}
        result.append(new_data)
    return result


def get_data(query=None):
    """
    Get data using the dissemin API
    https://dissem.in/api/search/?q=pregroup
    """
    dict_params = { "q": query, }
    result = []
    clean_params = {x: dict_params[x] for x in dict_params if dict_params[x]}
    params = urllib.parse.urlencode(dict_params)
    main_url = "https://dissem.in/api/search/?"
    req_url = main_url + params
    logger.debug("url = " + req_url)
    url = urllib.request.Request(
        req_url,
        headers={
            'User-Agent': papis.config.get('user-agent')
        }
    )
    jsondoc = urllib.request.urlopen(url).read().decode()
    paperlist = json.loads(jsondoc)
    docs = sum([dissemindoc_to_papis(d) for d in paperlist['papers']], [])
    return docs
