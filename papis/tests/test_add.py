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
        self.config_path = os.path.join(
            os.path.dirname(__file__),
            "resources",
            "config_1.ini"
        )
        # papis.config.set_config_file(self.config_path)
        # papis.commands.Command.config = papis.config.reset_configuration()
        # self.papers_dir = papis.config.get_configuration()["papers"]["dir"]

    @classmethod
    def tearDownClass(self):
        pass

    def test_existence(self):
        self.assertTrue(self.command is not None)

    def test_config_file_exists(self):
        self.assertTrue(os.path.exists(self.config_path))

    def test_help_message(self):
        # TODO: Check if thread returns succesfully or not
        import threading
        args = ("add", "-h")
        t = threading.Thread(
            target=papis.commands.main,
            args=[args]
        )
        t.start()
        t.join()
        self.assertFalse(t.isAlive())

    def test_mimetypes(self):
        test_data_path = os.path.join(papis.PAPISDIR, 'tests', 'data')
        exist_docs = [
            [os.path.join(test_data_path, 'text_file'), "text/plain"],
            [os.path.join(test_data_path, 'text_file.txt'), "text/plain"],
            [os.path.join(test_data_path, 'text_file.pdf'), "text/plain"],
            [os.path.join(test_data_path, 'pdf_file'), "application/pdf"],
            [os.path.join(test_data_path, 'pdf_file.pdf'), "application/pdf"],
            [os.path.join(test_data_path, 'pdf_file.txt'), "application/pdf"],
            [os.path.join(test_data_path, 'epub_file'), "application/epub+zip"],
            [os.path.join(test_data_path, 'epub_file.epub'), "application/epub+zip"],
            [os.path.join(test_data_path, 'epub_file.pdf'), "application/epub+zip"],
        ]
        for d in exist_docs:
            self.assertTrue(
                self.command.get_document_mimetype(d[0]) == d[1]
            )
        with self.assertRaises(FileNotFoundError):
          self.command.get_document_mimetype(os.path.join(test_data_path, "does_not_exist.pdf"))

    def test_extensions(self):
        test_data_path = os.path.join(papis.PAPISDIR, 'tests', 'data')
        exist_docs = [
            [os.path.join(test_data_path, 'text_file.txt'), "txt"],
            [os.path.join(test_data_path, 'text_file'), "txt"],
            [os.path.join(test_data_path, 'pdf_file'), "pdf"],
            [os.path.join(test_data_path, 'pdf_file.pdf'), "pdf"],
            [os.path.join(test_data_path, 'pdf_file.txt'), "pdf"],
            [os.path.join(test_data_path, 'epub_file'), "epub"],
            [os.path.join(test_data_path, 'epub_file.epub'), "epub"],
            [os.path.join(test_data_path, 'epub_file.pdf'), "epub"],
            [os.path.join(test_data_path, 'empty_file'), "txt"],
            [os.path.join(test_data_path, 'empty_file.mobi'), "mobi"],
        ]
        for d in exist_docs:
            self.assertTrue(
                self.command.get_document_extension(d[0]) == d[1]
            )
        with self.assertRaises(FileNotFoundError):
          self.command.get_document_mimetype(os.path.join(test_data_path, "does_not_exist.pdf"))
