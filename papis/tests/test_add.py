import unittest
import logging

from papis.commands.add import Add

logging.basicConfig(level=logging.DEBUG)


class TestClass(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.args = dict()
        self.command = Add()

    @classmethod
    def tearDownClass(self):
        pass

    def test_existence(self):
        self.assertTrue(self.command is not None)
        self.assertTrue(self.command.get_parser() is None)
