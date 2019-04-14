import re
import papis.downloaders.base
import bs4
import papis.document


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
        body = self._get_body()
        soup = bs4.BeautifulSoup(body, "html.parser")
        metas = soup.find_all(name="meta")
        data.setdefault('abstract', '')
        for meta in metas:
            if meta.attrs.get('name') == 'dc.Title':
                data['title'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'keywords':
                data['keywords'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'dc.Type':
                data['type'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'dc.Subject':
                data['note'] = meta.attrs.get('content')
            elif (meta.attrs.get('name') == 'dc.Identifier' and
                    meta.attrs.get('scheme') == 'doi'):
                data['doi'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'dc.Publisher':
                data['publisher'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'dc.Description':
                data['abstract'] += meta.attrs.get('content')

        articles = soup.find_all(name='article', attrs={'class': 'article'})
        author_list = []
        if articles:
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
