"""
ISBNPLUS Api Description
========================

Key             Description
---------------------------
q               Keywords, search for everything
p               Current page number, default is 1
a               Keywords, search for Author
c               Keywords, search for Catagory
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

An example of sucessful returns:
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
    International News In The Digital Age: East-West Perceptions Of A New World Order
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
    Journalism > International Cooperation; Citizen Journalism > Political Aspects; Communication, International > Political Aspects; Online Journalism; Mass Media And International Relations; Foreign News > Political Aspects;
    </category>
    </book>
    ...
"""
import xml.dom.minidom
import urllib.request# urlopen, Request
import urllib.parse# import urlencode
import bs4
import papis.config
import logging

logger = logging.getLogger('isbn')

ISBNPLUS_KEY = "98a765346bc0ffee6ede527499b6a4ee"
ISBNPLUS_APPID = "4846a7d1"
ISBNPLUS_BASEURL = "https://api-2445581351187.apicast.io:443/"
ISBNPLUS_BASEURL = "https://api-2445581351187.apicast.io/"

def get_data(
    query="",
    page=1,
    author="",
    category="",
    series="",
    title="",
    order="isbn",
    app_id=ISBNPLUS_APPID,
    app_key=ISBNPLUS_KEY
    ):
    results = []
    dict_params = {
        "q": query,
        "p": page,
        "a": author,
        "c": category,
        "s": series,
        "t": title,
        "order": order,
        "app_id": app_id,
        "app_key": app_key
    }
    params = urllib.parse.urlencode(
        {x:dict_params[x] for x in dict_params if dict_params[x]}
    )
    req_url = ISBNPLUS_BASEURL + "search?" + params
    logger.debug("url = " + req_url)
    url = urllib.request.Request(
        req_url,
        headers={
            'User-Agent': papis.config.get('user-agent')
        }
    )
    xmldoc = urllib.request.urlopen(url).read()
    root = bs4.BeautifulSoup(xmldoc, 'html.parser')

    for book in root.find_all('book'):
        book_data = book_to_data(book)
        results.append(book_data)
    logger.debug('%s records retrieved' % len(results))
    return results


def book_to_data(booknode):
    """Convert book xml node into dictionary

    :booknode: Bs4 book node
    :returns: Dictionary containing its data

    """
    book = dict()
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
        if key_pair[0] in book.keys():
            book[key_pair[1]] = book[key_pair[0]]
    return book
