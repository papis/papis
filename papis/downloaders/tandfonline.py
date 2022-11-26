import re
from typing import Optional, Any, Dict

import papis.downloaders.base
import papis.document


class Downloader(papis.downloaders.Downloader):
    re_clean = re.compile(r"(^\s*|\s*$|\s{2,}?|&)")
    re_comma = re.compile(r"(\s*,\s*)")
    re_add_dot = re.compile(r"(\b\w\b)")

    def __init__(self, url: str):
        papis.downloaders.Downloader.__init__(
            self, url, name="tandfonline")
        self.expected_document_extension = "pdf"
        self.priority = 10

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        return (Downloader(url)
                if re.match(r".*tandfonline.com.*", url) else None)

    def get_data(self) -> Dict[str, Any]:
        data = {}
        soup = self._get_soup()
        data.update(papis.downloaders.base.parse_meta_headers(soup))

        # `author` and `author_list` are already in meta_headers, but we
        # brute-force them here again to get exact affiliation information
        author_list = []
        authors = soup.find_all(name="span", attrs={"class": "contribDegrees"})
        for author in authors:
            affiliation = author.find_all("span", attrs={"class": "overlay"})
            if affiliation:
                # the span contains other things like the email, but we only
                # want the starting text with the affiliation address
                affiliation = next(affiliation[0].children)

                affiliation = self.re_comma.sub(
                    ", ", self.re_clean.sub("", affiliation))
                affiliation = [{"name": affiliation}]

            # find href="/author/escaped_fullname"
            fullname = author.find_all("a", attrs={"class": "entryAuthor"})
            fullname = fullname[0].get("href").split("/")[-1]

            import urllib.parse
            fullname = urllib.parse.unquote_plus(fullname)
            family, given = re.split(r",\s+", fullname)
            given = self.re_add_dot.sub(r"\1.", given)

            if "Reviewing Editor" in author.text:
                data["editor"] = (
                    papis.config.getstring("multiple-authors-format")
                    .format(au={"family": family, "given": given}))
                continue

            new_author = {"given": given, "family": family}
            if affiliation:
                new_author["affiliation"] = affiliation
            author_list.append(new_author)

        data["author_list"] = author_list
        data["author"] = papis.document.author_list_to_author(data)

        return data

    def get_bibtex_url(self) -> Optional[str]:
        if "doi" in self.ctx.data:
            url = ("http://www.tandfonline.com/action/downloadCitation"
                   "?format=bibtex&cookieSet=1&doi={doi}"
                   .format(doi=self.ctx.data["doi"]))
            self.logger.debug("bibtex url = '%s'", url)
            return url
        else:
            return None

    def get_document_url(self) -> Optional[str]:
        if "doi" in self.ctx.data:
            durl = ("http://www.tandfonline.com/doi/pdf/{doi}"
                    .format(doi=self.ctx.data["doi"]))
            self.logger.debug("doc url = '%s'", durl)
            return durl
        else:
            return None
