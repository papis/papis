# A lot of the logic of the below code, most significantly the API endpoints
# and metadata format, are based on https://github.com/xlcnd/isbnlib which is
# licensed under LGPL-3.0-or-later. Thanks @xlcnd for your work!
# See https://github.com/xlcnd/isbnlib for details
from __future__ import annotations

import re
from typing import Any

import requests

import papis.config
import papis.logging

logger = papis.logging.get_logger(__name__)

#: A list of services supported by :mod:`isbnlib`. Note that not all versions
#: have support for all of these versions.
ISBN_SERVICE_NAMES = ("goob", "openl", "wiki")
USER_AGENT = "Mozilla/5.0"


def format_title(title: str | None, subtitle: str | None = None) -> str:
    return (f"{title or ''} - {subtitle}" if subtitle else title or "").strip(
        ",.:;-_ "
    )


def strip_isbnlike(isbn_like: str) -> str:
    return "".join(c for c in isbn_like.upper() if c in "0123456789X")


def notisbn_fallback(isbn: str | None) -> bool:
    if isbn is None:
        return True
    # Remove non-required symbols such as hyphens or spaces
    isbn = strip_isbnlike(isbn)
    # Check length and position of X (only possible for ISBN-10 at position 10)
    if len(isbn) not in {10, 13} or isbn.find("X") not in {
        10 * (len(isbn) == 10) - 1,
        -1,
    }:
        return True
    # Validate checksum digit for ISBN-10
    if len(isbn) == 10:
        s = sum((10 - i) * int(isbn[i].replace("X", "10")) for i in range(10))
        return s % 11 != 0
    # Check currently available GS1 prefixes for ISBN-13
    if isbn[0:3] not in {"978", "979"}:
        return True
    # Validate checksum digit for ISBN-13
    return sum((1 + 2 * (i % 2)) * int(isbn[i]) for i in range(13)) % 10 != 0


def json_request(url: str) -> Any | None:
    r = requests.get(url, headers={"user-agent": USER_AGENT})
    if r.status_code != 200:
        return None
    try:
        data = r.json()
    except requests.exceptions.JSONDecodeError:
        return None
    return data


def googlebooks_isbn_search(query: str) -> str:
    # This assumes the query to be an ISBN
    query = strip_isbnlike(query)
    base_api_link = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
    data = json_request(requests.utils.requote_uri(base_api_link + query))
    if not data:
        return ""
    try:
        items = data["items"]
    except KeyError:
        return ""
    # Return the first ISBN that was provided by the API
    for i in items:
        for d in i.get("volumeInfo", {}).get("industryIdentifiers", {}):
            # isbnlib also doesn't consider ISBN-10 results
            if d.get("type") == "ISBN_13":
                return str(d["identifier"])
    return ""


def isbn_from_words_fallback(query: str) -> str:
    search_provider_url = "http://www.google.com/search?q="
    search_url = (
        search_provider_url
        + "ISBN+"
        + requests.utils.requote_uri(query.replace(" ", "+"))
    )
    r = requests.get(
        search_url,
        headers={
            "user-agent": USER_AGENT,
            "Content-Type": 'text/plain; charset="UTF-8"',
            "Content-Transfer-Encoding": "Quoted-Printable",
        },
    )
    regex = re.compile(
        r"97[89]-?[0-9]{10}|" r"97[89]-[-0-9]{13}|" r"[-0-9]{9,15}[0-9xX]",
        re.M,
    )
    potential_isbns = regex.findall(r.text)
    isbn = ""
    for i in potential_isbns:
        if not notisbn_fallback(i):
            isbn = googlebooks_isbn_search(i)
            if len(isbn) > 0:
                break
    return isbn


def meta_goob(isbn: str) -> dict[str, Any] | None:
    url = (
        "https://www.googleapis.com/books/v1/volumes?q={isbn_query}&fields="
        "items/volumeInfo(title,subtitle,authors,publisher,publishedDate,"
        "language,industryIdentifiers,description,imageLinks)&maxResults=1"
    )
    data = json_request(url.format(isbn_query="isbn:" + isbn))
    # Apparently this sometimes works when the previous request doesn't.
    # See: https://github.com/xlcnd/isbnlib/issues/119
    if not data:
        data = json_request(url.format(isbn_query=isbn))
    if not data:
        return None
    try:
        volumeinfo = data["items"][0]["volumeInfo"]
    except KeyError:
        return None
    # Check that ISBNs match
    ids = repr(volumeinfo.get("industryIdentifiers", ""))
    if "ISBN_13" in ids and isbn not in ids:
        raise ValueError("ISBN mismatch")
    meta: dict[str, Any] = {}
    meta["ISBN-13"] = isbn
    title = volumeinfo.get("title", "").replace(" :", ":")
    subtitle = volumeinfo.get("subtitle", "")
    meta["Title"] = format_title(title, subtitle)
    meta["Authors"] = volumeinfo.get("authors", [""])
    meta["Publisher"] = volumeinfo.get("publisher", "").strip('"')
    if "publishedDate" in volumeinfo and len(volumeinfo["publishedDate"]) >= 4:
        meta["Year"] = volumeinfo["publishedDate"][0:4]
    else:
        meta["Year"] = ""
    meta["Language"] = volumeinfo.get("language", "")
    return meta


def meta_openl(isbn: str) -> dict[str, Any] | None:
    url = (
        f"https://openlibrary.org/api/books.json?bibkeys=ISBN:{isbn}"
        "&jscmd=data"
    )
    data = json_request(url)
    if not data:
        return None
    try:
        volumeinfo = data[f"ISBN:{isbn}"]
    except KeyError:
        return None
    meta: dict[str, Any] = {}
    meta["ISBN-13"] = isbn
    title = volumeinfo.get("title", "").replace(" :", ":")
    subtitle = volumeinfo.get("subtitle", "")
    meta["Title"] = format_title(title, subtitle)
    meta["Authors"] = [
        a["name"] for a in volumeinfo.get("authors", [{"name": ""}])
    ]
    meta["Publisher"] = volumeinfo.get("publishers", [{"name": ""}])[0]["name"]
    if date := volumeinfo.get("publish_date", ""):
        match = re.search(r"\d{4}", date)
        meta["Year"] = match.group(0) if match else ""
    else:
        meta["Year"] = ""
    # It seems like open library does not provide the language
    meta["Language"] = ""
    return meta


def meta_wiki(isbn: str) -> dict[str, Any] | None:
    url = (
        f"https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/{isbn}"
    )
    data = json_request(url)
    if not data:
        return None
    try:
        volumeinfo = data[0]
    except KeyError:
        return None
    meta: dict[str, Any] = {}
    meta["ISBN-13"] = isbn
    title = volumeinfo.get("title", "").replace(" :", ":")
    meta["Title"] = format_title(title)
    meta["Authors"] = [" ".join(a) for a in volumeinfo.get("author", [""])]
    if not meta["Authors"] or len(meta["Authors"]) == 0:
        meta["Authors"] = [
            " ".join(a) for a in volumeinfo.get("contributor", [""])
        ]
    meta["Publisher"] = volumeinfo.get("publisher", "")
    if date := volumeinfo.get("date", ""):
        match = re.search(r"\d{4}", date)
        meta["Year"] = match.group(0) if match else ""
    else:
        meta["Year"] = ""
    # It seems like wiki does not provide the language
    meta["Language"] = ""
    return meta


def meta_fallback(isbn: str | None, service: str) -> dict[str, Any] | None:
    if not isbn or notisbn_fallback(isbn):
        return None
    if service == "goob":
        return meta_goob(isbn)
    elif service == "openl":
        return meta_openl(isbn)
    elif service == "wiki":
        return meta_wiki(isbn)
    else:
        return None


try:
    from isbnlib import notisbn

    __all__ = ["notisbn"]
except ImportError:
    notisbn = notisbn_fallback


def get_data(
    query: str = "", isbn_like: str = "", service: str | None = None
) -> list[dict[str, Any]]:
    logger.debug("Trying to retrieve ISBN from query: '%s'.", query)

    if service is None:
        service = papis.config.getstring("isbn-service")

    if service not in ISBN_SERVICE_NAMES:
        logger.error(
            "ISBN service '%s' is not known. Available services: '%s'.",
            service,
            "', '".join(ISBN_SERVICE_NAMES),
        )
        return []

    if isbn_like:
        isbn = strip_isbnlike(isbn_like)
    elif query:
        isbn = None
    else:
        raise ValueError("must provide either 'isbn_like' or 'query'")

    try:
        from isbnlib import ISBNLibException, isbn_from_words, meta

        try:
            if not isbn:
                isbn = isbn_from_words(query)
            data = meta(isbn, service=service)
        except ISBNLibException:
            return []
    except ImportError:
        if not isbn:
            isbn = isbn_from_words_fallback(query)
        data = meta_fallback(isbn, service=service)

    if isinstance(data, dict):
        return [data_to_papis(data)]
    else:
        logger.error("Could not retrieve ISBN data.")
        return []


def data_to_papis(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert data from isbnlib into Papis formatted data.

    :param data: Dictionary with data
    :returns: Dictionary with Papis key names
    """
    from papis.document import (
        KeyConversionPair,
        keyconversion_to_data,
        split_authors_name,
    )

    key_conversion = [
        KeyConversionPair(
            "authors", [{"key": "author_list", "action": split_authors_name}]
        ),
        KeyConversionPair(
            "isbn-13",
            [
                {"key": "isbn", "action": None},
                {"key": "isbn-13", "action": None},
            ],
        ),
        KeyConversionPair(
            "language",
            [{"key": "language", "action": lambda x: x if x else "en"}],
        ),
    ]

    data = {k.lower(): data[k] for k in data}
    result = keyconversion_to_data(
        key_conversion, data, keep_unknown_keys=True
    )

    # NOTE: 'isbnlib' does not give a type at all, so we can't know if this is
    # a proceeding or any other book-like format. Also, 'isbnlib' always uses
    # the 'book' type when converting to BibTeX, so we'll do the same.
    result["type"] = "book"

    return result
