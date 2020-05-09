import re
import papis.downloaders.fallback

from typing import Optional


class Downloader(papis.downloaders.fallback.Downloader):

    BASE = "https://citeseerx.ist.psu.edu"
    jsessionid = "012341666D7AD1C5C931FC0CFBA34BFA"

    def __init__(self, url: str):
        papis.downloaders.fallback.Downloader.__init__(self,
                                                       uri=url,
                                                       name="citeseerx")
        self.expected_document_extension = 'pdf'
        self.priority = 10

    @classmethod
    def match(cls,
              url: str) -> Optional[papis.downloaders.fallback.Downloader]:
        return (Downloader(url)
                if re.match(r".*citeseerx\.ist\.psu\.edu.*", url)
                else None)

    def get_document_url(self) -> Optional[str]:
        return ("{base}/viewdoc/download;jsessionid={jid}?"
                "doi={doi}&rep=rep1&type=pdf"
                .format(doi=self.ctx.data.get("doi"),
                        base=self.BASE,
                        jid=self.jsessionid))

    def download_bibtex(self) -> None:
        bibtex = self._get_soup().find_all(attrs=dict(id="bibtex"))
        if not bibtex:
            return None
        self.bibtex_data = ("\n".join(e.text for e in bibtex[0].find_all("p"))
                                .replace("\xa0", " "))
