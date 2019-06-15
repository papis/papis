import re

import papis.document
import papis.downloaders.base


def get_dropdown_affiliations(soup):
    # this function handles getting affiliations when they're described in the
    # separate `View Author Information` dropdown on acs.org. they are
    # in a <div class="affiliations"> with a list of <div class="aff-info">
    # for each existing affiliation.
    #
    # the affiliations seem to be presented in two ways
    #
    # 1. with children `<span>symbol</span>` and `<span>text</span>`, where
    # we just add it to the dictionary with the relevant symbol as a key.
    # this will get matched in `get_author_list` when going over the symbols
    # of each author.
    #
    # 2. just a `<span>text</span>` child. there are two subcases that need
    # to be handled here:
    #   2.1 sometimes the text contains a list of
    #   `<sup>symbol</sup> text, <sup>symbol</sup> text...`, when the
    #   affiliations are from different departments of the same institution.
    #   this gets split up and put in the dictionary.
    #
    #   2.2 no additional symbol info is given. in this case, we just add
    #   the affiliation with a key `affX`, where `X` is a counter for the
    #   unknown affiliations, starting at 0. these then get matched, in the
    #   same order to the authors in `get_author_list`, if possible.

    affs = soup.find_all(name='div', attrs={'class': 'aff-info'})
    if not affs:
        return {}

    affindex = 0
    affiliations = {}
    for aff in affs:
        spans = aff.find_all('span')
        symbol = []
        text = []
        if len(spans) == 1:
            children = list(spans[0].children)
            if len(children) == 1:
                symbol.append("aff{}".format(affindex))
                text.append(children[0])
                affindex += 1
            else:
                child_text = []
                for s, t in zip(children[0::2], children[1::2]):
                    symbol.append(s.text)
                    child_text.append(t.string.split(',')[0].strip())

                last_text = children[-1].string.split(',', maxsplit=1)[1]
                last_text = last_text.strip()
                text.extend(["{}, {}".format(t, last_text)
                             for t in child_text])
        else:
            symbol.append(spans[0].text)
            text.append(spans[1].text)

        for k, v in zip(symbol, text):
            affiliations[k.strip()] = v.strip()

    return affiliations


def get_author_list(soup):
    # this function tries to find all the authors which are given as
    # <span class="hlFld-ContribAuthor">author_info</span>.
    #
    # to get author names, we handle two different cases
    #
    # 1. the author name is in a <div class="loa-info-name"></div> tag
    # 2. the author name is in a <a>name</a> tag as the first child
    #
    # getting the affiliations is a bit more tricky and we handle two cases
    #
    # 1. the affiliations is in a popup with in a tag
    # <div class="lua-info-affiliations-info"> and can be obtained directly.
    #
    # 2. the affiliations are in a separate `View Author Information`
    # dropdown and a list was obtained from `get_dropdown_affiliations`.
    # this is sometimes ambiguous, so we handle three cases
    #   2.1 the author has a <span class="author-aff-symbol"> that directly
    #   matches to a key in the `affiliations` dict.
    #
    #   2.2 the author has an `author-aff-symbol`, but it doesn't match. in
    #   this case we look for a `affX` key in the order they are found in
    #   the author list (incrementing `curr_index`).
    #
    #   2.3 if the `affiliations` dict only has one unmatched key, just use
    #   that.

    affiliations = get_dropdown_affiliations(soup)

    author_list = []
    authors = soup.find_all(name='span',
            attrs={'class': re.compile('hlFld-ContribAuthor', re.I)})

    curr_index = 0
    symbol_key = {}
    for author in authors:
        # attempt to get affiliations
        author_affs = []

        if affiliations:
            affsymbols = author.find_all(name='span',
                    attrs={'class': 'author-aff-symbol'})
            if affsymbols:
                for s in affsymbols:
                    symbol = s.text.strip()
                    if symbol in affiliations:
                        author_affs.append(dict(name=affiliations[symbol]))
                        continue

                    if symbol not in symbol_key:
                        symbol_key[symbol] = "aff{}".format(curr_index)
                        curr_index += 1

                    symbol = symbol_key[symbol]
                    if symbol in affiliations:
                        author_affs.append(dict(name=affiliations[symbol]))

        if not author_affs:
            affs = author.find_all(name='div',
                    attrs={"class": "loa-info-affiliations-info"})
            if affs:
                author_affs.append(dict(name=affs[0].text))

        if not author_affs and len(affiliations) == 1:
            author_affs.append(dict(name=list(affiliations.values())[0]))

        # attempt to get author name
        fullname = author.find_all(name='div',
                attrs={'class': 'loa-info-name'})
        if fullname:
            fullname = fullname[0].text
        if not fullname:
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
    ACS_BIBTEX_URL = "http://pubs.acs.org/action/downloadCitation?format=bibtex&cookieSet=1&doi={data[doi]}"

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="acs")
        self.expected_document_extension = 'pdf'
        # It seems to be necessary so that acs lets us download the bibtex
        self.cookies = {'gdpr': 'true'}
        self.priority = 10

    @classmethod
    def match(cls, url):
        return Downloader(url) if re.match(r".*acs.org.*", url) else False

    def get_data(self):
        data = dict()
        soup = self._get_soup()
        data.update(papis.downloaders.base.parse_meta_headers(soup))

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
            url = self.ACS_BIBTEX_URL.format(data=self.ctx.data)
            self.logger.debug("bibtex url = %s" % url)
            return url
