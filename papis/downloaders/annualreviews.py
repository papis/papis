import re
import papis.downloaders.base
from typing import Optional, Dict, Any


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str):
        papis.downloaders.Downloader.__init__(
            self, url, name="annualreviews")
        self.expected_document_extension = 'pdf'
        self.priority = 10

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        if re.match(r".*annualreviews.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_document_url(self) -> Optional[str]:
        if 'doi' in self.ctx.data:
            doi = self.ctx.data['doi']
            url = "http://annualreviews.org/doi/pdf/{doi}".format(doi=doi)
            self.logger.debug("doc url = %s" % url)
            return url
        else:
            return None

    def get_bibtex_url(self) -> Optional[str]:
        if 'doi' in self.ctx.data:
            url = ("http://annualreviews.org/action/downloadCitation"
                   "?format=bibtex&cookieSet=1&doi={doi}"
                   .format(doi=self.ctx.data['doi']))
            self.logger.debug("bibtex url = %s" % url)
            return url
        else:
            return None

    def get_data(self) -> Dict[str, Any]:
        data = dict()
        soup = self._get_soup()
        data.update(papis.downloaders.base.parse_meta_headers(soup))

        if 'author_list' in data:
            return data

        # Read brute force the authors from the source
        author_list = []
        authors = soup.find_all(name='span', attrs={'class': 'contribDegrees'})
        cleanregex = re.compile(r'(^\s*|\s*$|&)')
        editorregex = re.compile(r'([\n|]|\(Reviewing\s*Editor\))')
        morespace = re.compile(r'\s+')
        for author in authors:
            affspan = author.find_all('span', attrs={'class': 'overlay'})
            afftext = affspan[0].text if affspan else ''
            fullname = re.sub(
                ',', '', cleanregex.sub('', author.text.replace(afftext, '')))
            splitted = re.split(r'\s+', fullname)
            cafftext = re.sub(' ,', ',',
                              morespace.sub(' ', cleanregex.sub('', afftext)))
            if 'Reviewing Editor' in fullname:
                data['editor'] = cleanregex.sub(
                    ' ', editorregex.sub('', fullname))
                continue
            given = splitted[0]
            family = ' '.join(splitted[1:])
            author_list.append(
                dict(
                    given=given,
                    family=family,
                    affiliation=[dict(name=cafftext)] if cafftext else []
                )
            )

        data['author_list'] = author_list
        data['author'] = papis.document.author_list_to_author(data)

        return data
