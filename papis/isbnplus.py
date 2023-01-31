"""
ISBNPLUS Api Description
========================

Key             Description
---------------------------
q               Keywords, search for everything
p               Current page number, default is 1
a               Keywords, search for Author
c               Keywords, search for Category
s               Keywords, search for book series
t               Keywords, search for book title
order           published - return results by published years, newest first
                isbn - return results by isbn numbers, smaller number first
                any - return results by isbn numbers, smaller number first
                any - return results by relevance, most relevant results first
                default is published
app_id          Application ID, required, you can get your application ID after
                login
app_key         Application Key, required, you can get your application key
                after login

An example of successful returns:
================================

    <?xml version="1.0" encoding="UTF-8"?>
    <response status="ok">
    <page name="search">
    <count>71</count>
    <total>71</total>
    <pages>8</pages>
    <current_page>1</current_page>
    <results>
    <book>
    <ISBNPlus_id>LOC.V40.196960-1-3374190</ISBNPlus_id>
    <link>http://isbnplus.org/9780415887229</link>
    <isbn13>9780415887229</isbn13>
    <isbn10>0415887224</isbn10>
    <title>
    International News In The Digital Age: East-West Perceptions Of A New World
    Order
    </title>
    <author>Judith Clarke; Michael Bromley</author>
    <published_place>New York</published_place>
    <publisher>Routledge</publisher>
    <published_year>2012</published_year>
    <pages>234</pages>
    <language>English</language>
    <lccn>2011008858</lccn>
    <format/>
    <series>Routledge research in journalism ( Volume 4 )</series>
    <reisbn>0</reisbn>
    <category>
    Journalism > International Cooperation; Citizen Journalism > Political
    Aspects; Communication, International > Political Aspects; Online
    Journalism; Mass Media And International Relations; Foreign News >
    Political Aspects;
    </category>
    </book>
    ...
"""
from typing import List, Dict, Any

import click
import bs4

import papis.utils
import papis.config
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)

ISBNPLUS_KEY = "98a765346bc0ffee6ede527499b6a4ee"  # type: str
ISBNPLUS_APPID = "4846a7d1"  # type: str
ISBNPLUS_BASEURL = "https://api-2445581351187.apicast.io:443/"  # type: str
# ISBNPLUS_BASEURL = "https://api-2445581351187.apicast.io/"  # type: str


def get_data(query: str = "",
             page: int = 1,
             author: str = "",
             category: str = "",
             series: str = "",
             title: str = "",
             order: str = "isbn",
             app_id: str = ISBNPLUS_APPID,
             app_key: str = ISBNPLUS_KEY
             ) -> List[Dict[str, Any]]:
    """Get documents from isbnplus"""
    session = papis.utils.get_session()
    response = session.get(
        "{}/search".format(ISBNPLUS_BASEURL),
        params={
            "q": query if query else None,
            "p": str(page),
            "a": author if author else None,
            "c": category if category else None,
            "s": series if series else None,
            "t": title if title else None,
            "order": order,
            "app_id": app_id,
            "app_key": app_key
        })
    if not response.ok:
        logger.error("An HTTP error (%d %s) was encountered for query: '%s'",
                     response.status_code, response.reason, query)
        return []

    root = bs4.BeautifulSoup(response.content, "html.parser")
    results = [book_to_data(book) for book in root.find_all("book")]
    logger.debug("%d records retrieved", len(results))

    return results


def book_to_data(booknode: "bs4.Tag") -> Dict[str, Any]:
    """Convert book xml node into dictionary

    :booknode: Bs4 book node
    :returns: Dictionary containing its data

    """
    book = {}
    keys_translate = [
        ("published_year", "year"), ("link", "url"),
    ]
    keys = [
        "title", "author", "language", "publisher", "pages", "isbn10",
        "isbn13", "link", "keywords", "published_year", "published_place",
        "series", "lccn", "ISBNPlus_id", "year"
    ]
    for key in keys:
        val_list = booknode.find_all(key)
        if len(val_list):
            book[key] = val_list[0].text
    for key_pair in keys_translate:
        if key_pair[0] in book:
            book[key_pair[1]] = book[key_pair[0]]
    return book


@click.command("isbnplus")
@click.pass_context
@click.help_option("--help", "-h")
@click.option("--query", "-q", default="", type=str)
@click.option("--author", "-a", default="", type=str)
@click.option("--title", "-t", default="", type=str)
def explorer(ctx: click.core.Context,
             query: str, author: str, title: str) -> None:
    """
    Look for documents on isbnplus.com

    Examples of its usage are

    papis explore isbnplus -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    logger.info("Looking up...")
    try:
        data = get_data(query=query, author=author, title=title)
    except Exception as ex:
        logger.error(ex)
        data = []
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("%s documents found", len(docs))
