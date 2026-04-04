from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from bs4 import Tag

from papis.downloaders import Downloader


def _parse_author(author: str) -> dict[str, str]:
    # NOTE: lingbuzz does store given and family names properly
    # NOTE: but they only seem to be accessible from the homepage
    # TODO: get them somehow
    split_name = author.split()
    return {
        "given": " ".join(split_name[:-1]),
        "family": split_name[-1]
    }


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


class LingbuzzDownloader(Downloader):
    """Retrieve documents from `LingBuzz <https://lingbuzz.net>`__"""

    def __init__(self, uri: str) -> None:
        super().__init__(
            uri,
            name="lingbuzz",
            expected_document_extension="pdf",
        )

    @classmethod
    def match(cls, url: str) -> Downloader | None:
        if re.match(r".*(lingbuzz\.net|ling\.auf\.net).*", url):
            return LingbuzzDownloader(url)
        else:
            return None

    def get_doi(self) -> str | None:
        # some authors provide doi in the "published in" field
        match = re.search(
            r"(?<=https:\/\/doi\.org\/)\S*",
            self.ctx.data.get("note", "")
        )
        if isinstance(match, re.Match):
            return match.group(0)
        else:
            return None

    def get_data(self) -> dict[str, Any]:
        from papis.document import author_list_to_author

        soup = self._get_soup()
        data: dict[str, Any] = {}

        center = soup.find("center")
        if isinstance(center, Tag):
            title_a = center.find("a")
            if title_a:
                data["title"] = title_a.text

            author_as = center.find_all("a")[1:]
            if author_as:
                data["author_list"] = [_parse_author(a.text) for a in author_as]
                data["author"] = author_list_to_author(data)

            date: str = center.contents[-1].get_text()
            if date:
                data["month"] = _parse_month(date)
                data["year"] = _parse_year(date)

            abstract_match = re.search(
                r"<\/center>\xa0<p><\/p>(.*?)<table",
                str(soup),
                flags=re.DOTALL
            )
            if isinstance(abstract_match, re.Match):
                data["abstract"] = abstract_match.group(1)

        table = soup.find("table")
        if isinstance(table, Tag):
            published_in = _get_table_cell_value(table, "Published in: ")
            if published_in:
                data["note"] = "Published in: " + published_in

            keywords = _get_table_cell_value(table, "keywords: ")
            if keywords:
                data["keywords"] = keywords

        data["type"] = "unpublished"
        data["url"] = self.uri

        return data

    def get_document_url(self) -> str | None:
        return self.uri + "/current"
