import unittest
import papis.downloaders
import papis.downloaders.utils


class TestRecognizer(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_main(self):
        self.assertTrue(papis.downloaders)

    def test_downloader_getter(self):
        # Function exists
        self.assertTrue(papis.downloaders.utils.get_downloader)
        aps = papis.downloaders.utils.get_downloader(
            "http://journals.aps.org/prb/abstract/10.1103/PhysRevB.95.085434"
        )
        self.assertTrue(len(aps.get_bibtex_url()))
        aps.download_bibtex()
        self.assertTrue(len(aps.get_bibtex_data()) != 0)
        print(aps.get_bibtex_data())
