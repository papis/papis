"""Taylor & Francis source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_FILE_URL = "https://www.tandfonline.com/doi/pdf/{doi}"
_BIBTEX_URL = (
    "https://www.tandfonline.com/action/downloadCitation?doi={doi}&format=bibtex"
)

#: FIXME: what other types are there?
tf_to_bibtex_converter: dict[str, str] = {
    "research-article": "article",
}


def _parse_year(date: str) -> int | None:
    match = re.match(r"(\d{4})-\d{1,2}-\d{1,2}", date)
    return int(match.group(1)) if match else None


def _parse_month(date: str) -> int | None:
    match = re.match(r"\d{4}-(\d{1,2})-\d{1,2}", date)
    return int(match.group(1)) if match else None


class TaylorAndFrancisHandler(WebsiteHandler):
    """Retrieve documents from `Taylor & Francis
    <https://www.tandfonline.com>`__.

    Scrapes the page's meta headers. The DOI is taken from the URL when the page does
    not contain one. The PDF and BibTeX URLs are derived from the DOI.
    """

    name = "taylorandfrancis"
    url_or_id_re = re.compile(r".*tandfonline\.com.*")

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data = super().scrape(evidence)

        if data:
            from papis.document import KeyConversionPair, keyconversion_to_data

            article_key_conversion = [
                KeyConversionPair(
                    "type",
                    [
                        {
                            "key": None,
                            "action": lambda x: tf_to_bibtex_converter.get(x, x),
                        }
                    ],
                ),
                KeyConversionPair(
                    "date",
                    [
                        {"key": "year", "action": _parse_year},
                        {"key": "month", "action": _parse_month},
                    ],
                ),
            ]

            data = keyconversion_to_data(
                article_key_conversion, data, keep_unknown_keys=True
            )

        if "doi" not in data:
            # NOTE: the DOI is the path tail after '/doi/(abs|full|pdf)/'
            match = re.search(r"/doi/(?:abs|full|pdf)/([^?#]+)", evidence.input)
            if match is not None:
                data["doi"] = match.group(1)

        return data

    def get_file_url(self, evidence: LookupInput) -> str | None:
        doi = self.data.get("doi")
        return _FILE_URL.format(doi=doi) if doi else None

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        doi = self.data.get("doi")
        return _BIBTEX_URL.format(doi=doi) if doi else None
