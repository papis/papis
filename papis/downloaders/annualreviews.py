import re
from typing import Any, ClassVar, Dict, Optional

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `Annual Reviews <https://www.annualreviews.org>`__"""

    DOCUMENT_URL: ClassVar[str] = "https://annualreviews.org/doi/pdf/{doi}"

    BIBTEX_URL: ClassVar[str] = (
        "https://annualreviews.org/action/downloadCitation"
        "?format=bibtex&cookieSet=1&doi={doi}"
        )

    def __init__(self, url: str) -> None:
        super().__init__(
            url, "annualreviews",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        if re.match(r".*annualreviews.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_document_url(self) -> Optional[str]:
        if "doi" in self.ctx.data:
            url = self.DOCUMENT_URL.format(doi=self.ctx.data["doi"])
            self.logger.debug("Using document URL: '%s'.", url)

            return url
        else:
            return None

    def get_bibtex_url(self) -> Optional[str]:
        if "doi" in self.ctx.data:
            url = self.BIBTEX_URL.format(doi=self.ctx.data["doi"])
            self.logger.debug("Using BibTeX URL: '%s'.", url)

            return url
        else:
            return None

    def get_data(self) -> Dict[str, Any]:
        data = {}
        soup = self._get_soup()
        data.update(papis.downloaders.base.parse_meta_headers(soup))

        if "author_list" in data:
            return data

        cleanregex = re.compile(r"(^\s*|\s*$|&)")
        editorregex = re.compile(r"([\n|]|\(Reviewing\s*Editor\))")
        morespace = re.compile(r"\s+")

        # Read brute force the authors from the source
        author_list = []
        authors = soup.find_all(name="span", attrs={"class": "contribDegrees"})

        for author in authors:
            affspan = author.find_all("span", attrs={"class": "overlay"})
            afftext = affspan[0].text if affspan else ""
            fullname = (
                cleanregex.sub("", author.text.replace(afftext, "")).replace(",", ""))
            split_fullname = re.split(r"\s+", fullname)
            cafftext = (
                morespace.sub(" ", cleanregex.sub("", afftext)).replace(" ,", ","))

            if "Reviewing Editor" in fullname:
                data["editor"] = cleanregex.sub(
                    " ", editorregex.sub("", fullname))
                continue

            given = split_fullname[0]
            family = " ".join(split_fullname[1:])
            author_list.append({
                "given": given,
                "family": family,
                "affiliation": [{"name": cafftext}] if cafftext else []
                }
            )

        data["author_list"] = author_list
        data["author"] = papis.document.author_list_to_author(data)

        return data
