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
        soup = self._get_soup()
        data.update(papis.downloaders.base.parse_meta_headers(soup))

        doi = soup.find_all(name="meta",
                attrs={"name": 'dc.Identifier', 'scheme': 'doi'})
        if doi:
            data['doi'] = doi[0].attrs.get('content')

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
            fullname = re.sub(',', '',
                        cleanregex.sub('', author.text.replace(afftext, '')))
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
