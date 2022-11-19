import re
from typing import Optional, Any, Dict, List

import papis.downloaders.base
import papis.document


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str):
        papis.downloaders.Downloader.__init__(
            self, url, name="springer")
        self.expected_document_extension = 'pdf'
        self.priority = 10

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        return (Downloader(url)
                if re.match(r".*link\.springer.com.*", url) else None)

    def get_data(self) -> Dict[str, Any]:
        data = dict()
        soup = self._get_soup()
        metas = soup.find_all(name="meta")
        author_list = []    # type: List[Dict[str, Any]]
        for meta in metas:
            if meta.attrs.get('name') == 'citation_title':
                data['title'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'dc.Subject':
                data['subject'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'citation_doi':
                data['doi'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'citation_publisher':
                data['publisher'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'citation_journal_title':
                data['journal'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'citation_issn':
                data['issn'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'citation_author':
                fnam = meta.attrs.get('content')
                fnams = re.split(r'\s+', fnam)
                author_list.append(
                    dict(
                        given=fnams[0],
                        family=' '.join(fnams[1:]),
                        affiliation=[]))
            elif meta.attrs.get('name') == 'citation_author_institution':
                if not author_list:
                    continue
                author_list[-1]['affiliation'].append(
                    dict(name=meta.attrs.get('content')))

        data['author_list'] = author_list
        data['author'] = papis.document.author_list_to_author(data)

        return data

    def get_bibtex_url(self) -> Optional[str]:
        if 'doi' in self.ctx.data:
            url = ("http://citation-needed.springer.com/v2/"
                   "references/{doi}?format=bibtex&amp;flavour=citation"
                   .format(doi=self.ctx.data['doi']))
            self.logger.debug("bibtex url = '%s'", url)
            return url
        else:
            return None

    def get_document_url(self) -> Optional[str]:
        if 'doi' in self.ctx.data:
            url = ("https://link.springer.com/content/pdf/"
                   "{doi}.pdf".format(doi=self.ctx.data['doi']))
            self.logger.debug("doc url = '%s'", url)
            return url
        else:
            return None
