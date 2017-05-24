import unittest
import logging
import papis.commands

from papis.commands.add import Add

logging.basicConfig(level=logging.DEBUG)

class CommandTest(papis.commands.Command):

    @classmethod
    def setUpClass(self):
        try:
            papis.commands.init()
        except:
            pass
        else:
            papis.commands.main()
        self.args = dict()
        self.command = Add()


class TestClass(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        try:
            papis.commands.init()
        except:
            pass
        self.args = dict()
        self.command = Add()

    @classmethod
    def tearDownClass(self):
        pass

    def test_existence(self):
        self.assertTrue(self.command is not None)
        self.assertTrue(self.command.get_parser() is None)

    def test_extension(self):
        docs = [
            ["blahblah.pdf", "pdf"],
            ["b.lahblah.pdf", "pdf"],
            ["no/extension/blahblah", "txt"],
            ["a/asdfsdf21/blahblah.epub", "epub"],
        ]
        for d in docs:
            self.assertTrue(
                self.command.get_document_extension(d[0]) == d[1]
            )

