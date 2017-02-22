import unittest
import logging
import tempfile
import os

import papis
import papis.bibtex

logging.basicConfig(level = logging.DEBUG)


class TestBibtex(unittest.TestCase):
    bib_file = None
    bib_entry = None

    @classmethod
    def setUpClass(self):
        self.bib_file = tempfile.mktemp()
        self.bib_entry = """
% some comments here
@article{PhysRevLett.105.040504,
  title     = {
  Room-Temperature Implementation of the Deutsch-Jozsa Algorithm with a Single
  Electronic Spin in Diamond
  },
  author    = {
              Shi,
% some comments here
               Fazhan and Rong,
               Xing and Xu,
               Nanyang and Wang,
               Ya and Wu,
               Jie and Chong,
               Bo and Peng,
               Xinhua and Kniepert,
               Juliane and Schoenfeld,
               Rolf-Simon and Harneit,
               Wolfgang and Feng,
               Mang and Du,
               Jiangfeng},
  journal   = {Phys. Rev. Lett.}, % some other comment here
  volume    = {105},
  issue     = {4},
  pages     = {040504},
  numpages  = {4},
  year      = {2010},
  month     = {Jul},
  publisher = {American Physical Society},
  doi       = {10.1103/PhysRevLett.105.040504},
  url       = {http://link.aps.org/doi/10.1103/PhysRevLett.105.040504}
}
        """
        fd = open(self.bib_file, "w+")
        fd.write(self.bib_entry)
        fd.close()


    @classmethod
    def tearDownClass(self):
        pass

    def test_bib_file_exists(self):
        self.assertTrue(os.path.exists(self.bib_file))
    def test_bibtexToDict(self):
        bib_dic = papis.bibtex.bibtexToDict(self.bib_file)
        keys = [
          "title",
          "author",
          "journal",
          "volume",
          "issue",
          "pages",
          "numpages",
          "year",
          "month",
          "publisher",
          "doi",
          "url"
          ]
        self.assertTrue(bib_dic["type"] == "article")
        for key in keys:
            print(key)
            self.assertTrue(key in list(bib_dic.keys()))
    def test_bibkeys_exist(self):
        self.assertTrue(len(papis.bibtex.bibtexKeys) != 0)
    def test_bibtypes_exist(self):
        self.assertTrue(len(papis.bibtex.bibtexTypes) != 0)
