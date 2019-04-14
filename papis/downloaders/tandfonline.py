import re
import papis.downloaders.base
import bs4
import papis.document


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="tandfonline")
        self.expected_document_extension = 'pdf'
        self.priority = 10

    @classmethod
    def match(cls, url):
        return (Downloader(url)
                if re.match(r".*tandfonline.com.*", url) else False)

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
                data['subject'] = meta.attrs.get('content')
            elif (meta.attrs.get('name') == 'dc.Identifier' and
                    meta.attrs.get('scheme') == 'doi'):
                data['doi'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'dc.Publisher':
                data['publisher'] = meta.attrs.get('content')
            elif meta.attrs.get('name') == 'dc.Description':
                data['abstract'] += meta.attrs.get('content')

        author_list = []
        authors = soup.find_all(name='span', attrs={'class': 'contribDegrees'})
        cleanregex = re.compile(r'(^\s*|\s$|&)')
        morespace = re.compile(r'\s\+')
        for author in authors:
            affspan = author.find_all('span', attrs={'class': 'overlay'})
            afftext = affspan[0].text if affspan else ''
            fullname = cleanregex.sub('', author.text.replace(afftext, ''))
            splitted = re.split(r'\s*', fullname)
            cafftext = re.sub(' ,', ',',
                              morespace.sub(' ', cleanregex.sub('', afftext)))
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

    def get_bibtex_url(self):
        if 'doi' in self.ctx.data:
            url = (
                "http://www.tandfonline.com/action/downloadCitation"
                "?format=bibtex&cookieSet=1&doi=%s" % self.ctx.data['doi'])
            self.logger.debug("bibtex url = %s" % url)
            return url

    def get_document_url(self):
        if 'doi' in self.ctx.data:
            durl = (
                "http://www.tandfonline.com/doi/pdf/{doi}"
                .format(doi=self.ctx.data['doi']))
            self.logger.debug("doc url = %s" % durl)
            return durl
