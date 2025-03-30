from typing import List, Dict, Any

import click

import papis.config
import papis.utils
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)

DISSEMIN_API_URL = "https://dissem.in/api/search/"


def dissemin_authors_to_papis_authors(data: Dict[str, Any]) -> Dict[str, Any]:
    new_data: Dict[str, Any] = {}
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
            ["{} {}".format(a["given_name"], a["surname"]) for a in authors])
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
    with papis.utils.get_session() as session:
        response = session.get(DISSEMIN_API_URL, params={"q": query})

    if not response.ok:
        logger.error("An HTTP error (%d %s) was encountered for query: '%s'.",
                     response.status_code, response.reason, query)
        return []

    from itertools import chain

    paperlist = response.json()
    return list(
        chain.from_iterable(dissemindoc_to_papis(d) for d in paperlist["papers"])
    )


@click.command("dissemin")
@click.pass_context
@click.help_option("--help", "-h")
@click.option("--query", "-q", default="", type=str)
def explorer(ctx: click.core.Context, query: str) -> None:
    """
    Look for documents on `dissem.in <https://dissem.in/>`__.

    For example, to look for a document with the author "Albert Einstein" and
    open it with Firefox, you can call

    .. code:: sh

        papis explore \\
            dissemin -q 'Albert einstein' \\
            pick \\
            cmd 'firefox {doc[url]}'
    """
    logger.info("Looking up Dissemin documents...")

    data = get_data(query=query)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("Found %s documents.", len(docs))
