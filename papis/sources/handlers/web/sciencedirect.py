"""ScienceDirect source handler."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler, parse_meta_headers

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


# A list of ScienceDirect tags that we consider to be text in _parse_full_abstract
_KNOWN_TEXT = {"inf", "__text__", "simple-para"}

#: Metadata is embedded as a JavaScript assignment
_PRELOADED_STATE = "window.__PRELOADED_STATE__"


def _parse_author_list(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract the author list from ScienceDirect's embedded JSON data.

    This seems to be a data structure of the form

    .. code::

        entry {
            "#name": <key-name>,
            "_": <string>,
            "$": <dict[str, entry]>,
            "$$": <list[entry]>,
        }

    defined recursively, so maybe there's a better way to traverse it, but for now this
    is sufficient and no need to be too fancy about it.
    """
    if "#name" not in data or "$$" not in data:
        return [{}]

    def _parse_author(author: dict[str, Any]) -> dict[str, Any]:
        # NOTE: this seems fairly fragile, so hopefully it won't break too badly
        if "$$" not in author:
            return {}

        names = author["$$"]
        if len(names) < 2:
            return {}

        given, family = names[:2]
        assert given["#name"] == "given-name"
        assert family["#name"] == "surname"

        return {"given": given["_"], "family": family["_"], "affiliation": []}

    assert data["#name"] == "author-group"
    return [_parse_author(a) for a in data["$$"] if a["#name"] == "author"]


def _parse_full_abstract(data: list[dict[str, Any]]) -> str:
    """Concatenate the ``abstract-sec`` text of the embedded JSON data.

    `data` contains `abstract-sec` sections with `__text__` entries that we retrieve and
    concatenate to get the full abstract text.
    """

    def reconstruct_text(entry: Any) -> str:
        if isinstance(entry, dict):
            return str(entry["_"]) if entry.get("#name") in _KNOWN_TEXT else ""
        elif isinstance(entry, list):
            blocks = []
            for item in entry:
                p = reconstruct_text(item.get("$$", item))
                if p:
                    blocks.append(p)

            # FIXME: this can also be separate paragraphs, so concatenating them
            # with no newlines is not great, but that would be extra work
            return "".join(blocks)
        else:
            return ""

    for entry in data:
        d = entry.get("$$")
        if not d:
            continue

        section_title = d[0].get("_").lower()
        if section_title != "abstract":
            continue

        paragraphs = []
        for subentry in d:
            if subentry.get("#name") == "abstract-sec":
                text = reconstruct_text(subentry["$$"])
                if text:
                    paragraphs.append(text)

        if paragraphs:
            return "\n\n".join(paragraphs)

    return ""


class ScienceDirectHandler(WebsiteHandler):
    """Retrieve documents from `ScienceDirect <https://www.sciencedirect.com>`__.

    Scrapes the page's meta headers plus metadata from the embedded
    ``window.__PRELOADED_STATE__`` data. No document or BibTeX export URL is derived
    since they don't exist.
    """

    name = "sciencedirect"
    url_or_id_re = re.compile(r".*\.sciencedirect\.com.*")

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if evidence.content is None:
            return data

        from papis.document import author_list_to_author

        soup = self._get_soup(evidence.content)

        # get authors
        rawdata: dict[str, Any] | None = None
        for script in soup.find_all(name="script"):
            text = script.string or ""
            if _PRELOADED_STATE not in text:
                continue

            index = text.find("{", text.find(_PRELOADED_STATE))
            if index < 0:
                continue

            rawdata, _ = json.JSONDecoder().raw_decode(text, index)
            break

        self.logger.debug("Found embedded article data: %s.", rawdata is not None)

        if rawdata is not None:
            data["author_list"] = _parse_author_list(rawdata["authors"]["content"][0])
            data["author"] = author_list_to_author(data)

        # get main citation data
        # NOTE: this is second because the data is likely more accurate
        data.update(parse_meta_headers(soup))
        data["url"] = evidence.input

        # get full abstract
        if rawdata is not None:
            full_abstract = _parse_full_abstract(rawdata["abstracts"]["content"])
            if full_abstract:
                data["abstract"] = full_abstract

        if "firstpage" in data and "lastpage" in data:
            data["pages"] = "{}-{}".format(data["firstpage"], data["lastpage"])

        if "publication_date" in data:
            data["year"], _, _ = data["publication_date"].split("/")

        return data
