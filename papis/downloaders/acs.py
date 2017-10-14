import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="acs")
        self.expected_document_format = 'pdf'

    @classmethod
    def match(cls, url):
        """
        >>> Downloader.match(\
                'blah://pubs.acs.org/doi/abs/10.1021/acs.jchemed.6b00559'\
            ) is False
        False
        >>> Downloader.match(\
                'blah://pubs.acs.org/!@#!@$!%!@%!$che.6b00559'\
            ) is False
        False
        >>> Downloader.match(\
                'acs.com/!@#!@$!%!@%!$chemed.6b00559'\
            ) is False
        True
        """
        if re.match(r".*acs.org.*", url):
            return Downloader(url)
        else:
            return False

    def get_doi(self):
        # http://pubs.acs.org/doi/whatever/10.1021/acs.jchemed.6b00559
        mdoi = re.match(r'.*acs.org/doi/[^/]+/(.*)', self.get_url())
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            self.logger.debug("[doi] = %s" % doi)
            return doi
        else:
            self.logger.error("Doi not found!!")

    def get_document_url(self):
        # http://pubs.acs.org/doi/pdf/10.1021/acs.jchemed.6b00559
        durl = "http://pubs.acs.org/doi/pdf/" + self.get_doi()
        self.logger.debug("[doc url] = %s" % durl)
        self.logger.error("Retrieving urls does not work for acs yet")
        raise Exception
        return durl

    def get_bibtex_url(self):
        url = "http://pubs.acs.org/action/downloadCitation"\
              "?format=bibtex&cookieSet=1&doi=%s" % self.get_doi()
        self.logger.debug("[bibtex url] = %s" % url)
        return url

# vim-run: python3 -m doctest %
