from typing import List, Dict, Any

import click

import papis.config
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)


def dissemin_authors_to_papis_authors(data: Dict[str, Any]) -> Dict[str, Any]:
    new_data = {}  # type: Dict[str, Any]
    if "authors" in data:
        authors = []
        for author in data["authors"]:
            # keys = ('first', 'last')
            authors.append({
                "given_name": author["name"]["first"],
                "surname": author["name"]["last"]
                }
            )
        new_data["author_list"] = authors
        new_data["author"] = ",".join(
            ["{a[given_name]} {a[surname]}".format(a=a) for a in authors])
    return new_data


def dissemindoc_to_papis(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    common_data = {}
    result = []
    common_data["title"] = data.get("title")
    common_data["type"] = data.get("type")
    common_data.update(dissemin_authors_to_papis_authors(data))
    for record in data["records"]:
        new_data = {}
        new_data.update(common_data)
        new_data.update(record)
        new_data["doc_url"] = new_data.get("pdf_url")
        new_data["url"] = new_data.get("splash_url")
        new_data["tags"] = new_data.get("keywords")

        new_data = {key: new_data[key] for key in new_data if new_data[key]}
        result.append(new_data)
    return result


def get_data(query: str = "") -> List[Dict[str, Any]]:
    """
    Get data using the dissemin API
    https://dissem.in/api/search/?q=pregroup
    """
    import urllib.parse
    import urllib.request

    dict_params = {"q": query}
    params = urllib.parse.urlencode(dict_params)
    main_url = "https://dissem.in/api/search/?"
    req_url = main_url + params
    logger.debug("url = '%s'", req_url)
    url = urllib.request.Request(
        req_url,
        headers={
            "User-Agent": str(papis.config.get("user-agent"))
        }
    )
    jsondoc = urllib.request.urlopen(url).read().decode()

    import json
    paperlist = json.loads(jsondoc)
    return sum([dissemindoc_to_papis(d) for d in paperlist["papers"]], [])


@click.command("dissemin")
@click.pass_context
@click.help_option("--help", "-h")
@click.option("--query", "-q", default="", type=str)
def explorer(ctx: click.core.Context, query: str) -> None:
    """
    Look for documents on dissem.in

    Examples of its usage are

    papis explore dissemin -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    logger.info("Looking up...")

    data = get_data(query=query)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("%s documents found", len(docs))
