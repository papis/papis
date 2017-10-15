import re
import bs4
import papis.downloaders.base
import urllib.request


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="libgen")

    @classmethod
    def match(cls, url):
        # http://libgen.io/ads.php?md5=CBA569C45B32CA3DF52E736CD8EF6340
        if re.match(r".*libgen.*md5=.*", url):
            return Downloader(url)
        else:
            return False

    def get_md5(self):
        return re.match(r'.*md5=([A-Z0-9]+).*', self.get_url()).group(1)

    def download_bibtex(self):
        url = 'http://libgen.io/ads.php?md5=%s' % self.get_md5()
        raw_data = urllib.request.urlopen(url)\
            .read()\
            .decode('utf-8')
        soup = bs4.BeautifulSoup(raw_data, "html.parser")
        textareas = soup.find_all("textarea")
        if not textareas:
            return False
        self.bibtex_data = textareas[0].text
