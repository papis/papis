import re
import bs4
import papis.downloaders.base
import urllib.request


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url)

    @classmethod
    def match(cls, url):
        # http://libgen.io/ads.php?md5=CBA569C45B32CA3DF52E736CD8EF6340
        if re.match(r".*libgen.*", url):
            return Downloader(url)
        else:
            return False

    def downloadBibtex(self):
        raw_data = urllib.request.urlopen(self.getUrl())\
            .read()\
            .decode('utf-8')
        soup = bs4.BeautifulSoup(raw_data, "html.parser")
        textareas = soup.find_all("textarea")
        if not textareas:
            return False
        self.bibtex_data = textareas[0].text
