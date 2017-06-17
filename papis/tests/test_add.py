import unittest
import logging
import papis.commands
import papis.config
import os

logging.basicConfig(level=logging.DEBUG)

class CommandTest(unittest.TestCase):

    @classmethod
    def setUpClass(self, args=[]):
        try:
            papis.commands.init()
        except:
            pass


class TestAdd(CommandTest):

    @classmethod
    def setUpClass(self):
        super(self, self).setUpClass()
        self.args = dict()
        self.command = papis.commands.get_commands()["add"]

    @classmethod
    def tearDownClass(self):
        pass

    def test_existence(self):
        self.assertTrue(self.command is not None)

    def test_config_file_exists(self):
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    os.path.dirname(__file__),
                    "resources",
                    "config_1.ini"
                )
            )
        )

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

