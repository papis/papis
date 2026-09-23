"""LingBuzz source handler."""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from bs4 import Tag

    from papis.sources.handler import LookupInput


#: The abstract is the text between the centered metadata block and the details table
_ABSTRACT_RE = re.compile(
    r"</center>\xa0<p></p>(.*?)<table",
    re.DOTALL,
)


def _parse_month(date: str) -> int:
    return datetime.strptime(date, "%B %Y").month


def _parse_year(date: str) -> int:
    return datetime.strptime(date, "%B %Y").year


def _get_table_cell_value(table: Tag, label: str) -> str:
    label_cell = table.find("td", string=label)
    if label_cell:
        value_cell = label_cell.next_sibling
        if value_cell and isinstance(value_cell.text, str):
            return value_cell.text
    return ""


class LingbuzzHandler(WebsiteHandler):
    """Retrieve documents from `LingBuzz <https://lingbuzz.net>`__.

    Scrapes the page's centered title/author block and details table. The PDF URL is
    built from the page URL.
    """

    name = "lingbuzz"
    url_or_id_re = re.compile(r".*(lingbuzz\.net|ling\.auf\.net).*")

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        if evidence.content is None:
            return {}

        from papis.document import author_list_to_author, split_author_name

        soup = self._get_soup(evidence.content)
        data: dict[str, Any] = {}

        center = soup.find("center")
        if center is not None:
            title_a = center.find("a")
            if title_a:
                data["title"] = title_a.text

            author_as = center.find_all("a")[1:]
            if author_as:
                data["author_list"] = [split_author_name(a.text) for a in author_as]
                data["author"] = author_list_to_author(data)

            date: str = center.contents[-1].get_text()
            if date:
                data["month"] = _parse_month(date)
                data["year"] = _parse_year(date)

            abstract_match = _ABSTRACT_RE.search(str(soup))
            if abstract_match:
                data["abstract"] = abstract_match.group(1)

        table = soup.find("table")
        if table is not None:
            published_in = _get_table_cell_value(table, "Published in: ")
            if published_in:
                data["note"] = "Published in: " + published_in

            keywords = _get_table_cell_value(table, "keywords: ")
            if keywords:
                data["keywords"] = keywords

        data["type"] = "unpublished"
        data["url"] = evidence.input

        return data

    def get_doi(self, evidence: LookupInput) -> str | None:
        match = re.search(r"(?<=https://doi\.org/)\S*", self.data.get("note", ""))
        return match.group(0) if match else None

    def get_file_url(self, evidence: LookupInput) -> str | None:
        return f"{self.url}/current"
