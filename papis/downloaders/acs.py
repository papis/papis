import re
import bs4

import papis.document
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="acs")
        self.expected_document_extension = 'pdf'
        # It seems to be necessary so that acs lets us download the bibtex
        self.cookies = { 'gdpr': 'true', }
        self.priority = 10

    @classmethod
    def match(cls, url):
        return Downloader(url) if re.match(r".*acs.org.*", url) else False

    def get_data(self):
        data = dict()
        soup = self._get_soup()
        data.update(papis.downloaders.base.parse_meta_headers(soup))

        articles = soup.find_all(name='article', attrs={'class': 'article'})
        if not articles:
            return data

        author_list = []
            article = articles[0]
            for author in article.find_all(name='a', attrs={'id': 'authors'}):
                author_list.append(
                    dict(
                        given=author.text.split(' ')[0],
                        family=' '.join(author.text.split(' ')[1:]),
                        affiliation=[]
                    )
                )
            year = article.find_all(
                    name='span', attrs={'class': 'citation_year'})
            if year:
                data['year'] = year[0].text
            volume = article.find_all(
                    name='span', attrs={'class': 'citation_volume'})
            if volume:
                data['volume'] = volume[0].text
            affiliations = article.find_all(
                    name='div', attrs={'class': 'affiliations'})
            if affiliations:
                # TODO: There is no guarantee that the affiliations thus
                # retrieved are ok, however is better than nothing.
                # They will most probably don't match the authors
                for aff in affiliations[0].find_all(name='div'):
                    for author in author_list:
                        author['affiliation'].append(
                            dict(name=aff.text.replace('\n', ' ')))

        data['author_list'] = author_list
        data['author'] = papis.document.author_list_to_author(data)

        return data

    def get_document_url(self):
        if 'doi' in self.ctx.data:
            return "http://pubs.acs.org/doi/pdf/" + self.ctx.data['doi']

    def get_bibtex_url(self):
        if 'doi' in self.ctx.data:
            url = ("http://pubs.acs.org/action/downloadCitation"
                  "?format=bibtex&cookieSet=1&doi=%s" % self.ctx.data['doi'])
            self.logger.debug("bibtex url = %s" % url)
            return url
