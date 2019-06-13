import re
import bs4

import papis.document
import papis.downloaders.base

def get_affiliations(soup):
    affiliations = {}

    # affiliations are in a <div class="affiliations"> with a list of
    # <div class="aff-info"> for each existing affilition
    affs = soup.find_all(name='div', attrs={'class': 'aff-info'})

    if not affs:
        return affiliations

    for aff in affs:
        spans = aff.find_all('span')
        # each affilition has a
        #   <span>some_symbol</span>
        #   <span>affilition_text</span>
        # or just the text if all the authors are the same
        if len(spans) == 1:
            symbol = "default"
            text = spans[0].text.strip()
        else:
            symbol = spans[0].text.strip()
            text = spans[1].text.strip()

        affiliations[symbol] = text

    return affiliations


def get_author_list(soup):
    affiliations = get_affiliations(soup)

    author_list = []
    authors = soup.find_all(name='span',
            attrs={'class': re.compile('hlFld-ContribAuthor', re.I)})

    for author in authors:
        # each author has a list of "author-aff-symbol"s that we can match to
        # the data we have in `affiliations`
        affs = author.find_all(name='span',
                attrs={'class': 'author-aff-symbol'})

        author_affs = []
        if affs:
            for a in affs:
                symbol = a.text.strip()
                if symbol in affiliations:
                    author_affs.append(dict(name=affiliations[symbol]))
        elif affiliations:
            author_affs.append(dict(name=affiliations["default"]))

        # author name is in the <a> tag
        fullname = author.find_all(name='a')[0].text
        splitted = re.split(r'\s+', fullname)
        family = splitted[-1]
        given = " ".join(splitted[:-1])

        author_list.append(dict(
            family=family,
            given=given,
            affiliation=author_affs))

    return author_list


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

        # find authors
        author_list = get_author_list(soup)
        if author_list:
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
