import re
import papis.downloaders.base
import urllib


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="fallback"
        )
        #self.expected_document_extension = 'pdf'

    @classmethod
    def match(cls, url):
        return Downloader(url)

    def get_doi(self):
        doi_regex = re.compile(r'doi:([^"\'<>#?&]+)', re.I)
        # This should be last, since many references are given by this
        https_regex = re.compile(r'doi.org/([^"\'<>#?&]+)', re.I)
        # Sometimes is in the javascript defined
        var_doi = re.compile(r'var *doi *= *"([^"]+)"', re.I)
        body = self.session.get(self.get_url()).content.decode('utf-8')
        self.logger.info('trying to parse doi...')
        for regex in [doi_regex, https_regex, var_doi]:
            miter = regex.finditer(body)
            try:
                m = next(miter)
                if m:
                    doi = m.group(1)
                    print(m)
                    self.logger.info('got doi {0}'.format(doi))
                    return doi
            except StopIteration:
                pass
