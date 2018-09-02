import unittest
import papis.downloaders
import papis.downloaders.utils
from papis.downloaders.aps import Downloader


class TestRecognizer(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_main(self):
        self.assertTrue(papis.downloaders)

    def test_match(self):
        assert(
            Downloader.match(
                'blah://pubs.aps.org/doi/abs/10.1021/acs.jchemed.6b00559'
            )
        )
        assert(
            Downloader.match(
                'blah://pubs.aps.org/!@#!@$!%!@%!$che.6b00559'
            )
        )
        assert(
            Downloader.match(
                'aps.com/!@#!@$!%!@%!$chemed.6b00559'
            ) is False
        )

    def test_downloader_getter(self):
        self.assertTrue(papis.downloaders.utils.get_downloader)
        aps = papis.downloaders.utils.get_downloader(
            "http://journals.aps.org/prb/abstract/10.1103/PhysRevB.95.085434"
        )
        self.assertTrue(len(aps.get_bibtex_url()))
        aps.download_bibtex()
        self.assertTrue(len(aps.get_bibtex_data()) != 0)
        print(aps.get_bibtex_data())
