import re
from typing import Any, Dict, Optional

import papis.document
import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    def __init__(self, url: str) -> None:
        super().__init__(
            url,
            name="acl",
            expected_document_extension="pdf",
            priority=10,
        )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        return Downloader(url) if re.match(r".*aclanthology\.org.*", url) else None

    def fetch_acl_data(self) -> Dict[str, str]:
        try:
            elem = self._soup.find("div", "row acl-paper-details").find("dl")  # type: ignore
        except AttributeError:
            elem = None

        data = {}
        if elem is not None:
            for dt in elem.find_all("dt"):
                if "Anthology ID" in dt.text:
                    data["acl_anthology_id"] = dt.find_next_sibling().text
                if "Code" in dt.text:
                    data["code"] = dt.find_next_sibling().find("a").attrs["href"]

        return data

    def get_data(self) -> Dict[str, Any]:
        soup = self._get_soup()
        data = papis.downloaders.base.parse_meta_headers(soup)

        # wrong field scraped: use bibtex to get correct abstract
        data.pop("abstract")

        data.update(self.fetch_acl_data())

        if "publication_date" in data:
            dates = data["publication_date"].split("/")
            data["year"] = dates[0]

        return data

    def get_bibtex_url(self) -> Optional[str]:
        if self.ctx.data.get("acl_anthology_id") is not None:
            acl_anthology_id = self.ctx.data.get("acl_anthology_id")
            url = f"https://aclanthology.org/{acl_anthology_id}.bib"
            self.logger.debug("Using BibTeX URL: '%s'.", url)
            return url

        return None

    def get_document_url(self) -> Optional[str]:
        if "pdf_url" in self.ctx.data:
            url = str(self.ctx.data["pdf_url"])
            self.logger.debug("Using document URL: '%s'.", url)
            return url

        return None


if __name__ == "__main__":
    TEST_CASES = [
        (
            "https://aclanthology.org/N04-1001",
            {"acl_anthology_id": "N04-1001"},
        ),
        (
            "https://aclanthology.org/2021.naacl-main.208/",
            {"acl_anthology_id": "2021.naacl-main.208"},
        ),
    ]
    for url, y_true in TEST_CASES:
        d = Downloader(url)
        d.fetch_data()

        print(f"Test: {url}")
        print("Fetched:")
        print(f"\t {d.ctx.data}")
        assert d.ctx.data["acl_anthology_id"] == y_true["acl_anthology_id"]
        print("\n\n")
