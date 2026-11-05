"""ACL Anthology source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


class ACLHandler(WebsiteHandler):
    """Retrieve documents from the `ACL Anthology <https://aclanthology.org>`__.

    Scrapes the page's meta headers plus the anthology details table. The BibTeX URL is
    derived from the scraped anthology ID.
    """

    name = "acl"
    url_or_id_re = re.compile(r".*aclanthology\.org.*")

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data = super().scrape(evidence)
        if not data:
            return data

        # wrong field scraped: use bibtex to get correct abstract
        data.pop("abstract", None)

        if evidence.content is not None:
            soup = self._get_soup(evidence.content)
            elem = soup.find("div", "row acl-paper-details")
            if elem is not None:
                elem = elem.find("dl")

            if elem is not None:
                for dt in elem.find_all("dt"):
                    if "Anthology ID" in dt.text:
                        data["acl_anthology_id"] = dt.find_next_sibling().text
                    elif "Code" in dt.text:
                        link = dt.find_next_sibling().find("a")
                        if link is not None:
                            data["code"] = link.attrs["href"]

        if "publication_date" in data:
            data["year"] = data["publication_date"].split("/")[0]

        return data

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        anthology_id = self.data.get("acl_anthology_id")
        if anthology_id is not None:
            return f"https://aclanthology.org/{anthology_id}.bib"

        return None
