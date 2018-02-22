import unittest
import logging
import papis.commands
import papis.config
from papis.api import status
import os

logging.basicConfig(level=logging.DEBUG)

# FIXME: those can be moved to utils


def filehash(f: str) -> str:
    '''Return the sha256 hash of a the file `f`. File `f` must exists'''
    import hashlib
    m = hashlib.sha256()
    hs = ""
    with open(f, "r") as src:
        m.update(src.read().encode('utf-8'))
        hs = m.hexdigest()
    return hs


def files_are_equal(file_a: str, file_b: str) -> bool:
    '''Helper function that checks that the `file_a` file hash is the same as
    the `file_b`. Returns `False` if one of the file does not exists
    or if hashes are different, else `True`'''
    if os.path.isfile(file_a) and os.path.isfile(file_b):
        return filehash(file_a) == filehash(file_b)

    return False


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

    def test_add_file(self):
        args = ("add",
                os.path.join(os.path.dirname(__file__),
                             "resources",
                             "example_document.txt"))
        output = papis.commands.main(args)

        doc_data = {'author': "Unknown"}

        cmd = papis.commands.add.Command()
        expected_folder_name = cmd.get_hash_folder(
            doc_data,
            os.path.join(
                os.path.dirname(__file__),
                "resources",
                "example_document.txt"))

        lib_dir = os.path.expanduser(papis.config.get('dir'))
        out_dir = os.path.join(lib_dir, expected_folder_name)
        # path exists
        self.assertTrue(os.path.isdir(out_dir))
        # file exists
        self.assertTrue(os.path.isfile(
            os.path.join(out_dir, "example_document.txt")))

        # FIXME: check output folder and file!
        self.assertTrue(output == 0)

        args = ("rm", "-f",
                "example_document.txt")
        output = papis.commands.main(args)
        # FIXME: check output folder and file!
        self.assertTrue(output == status.success)

    def test_add_missing(self):
        args = ("add",
                os.path.join(os.path.dirname(__file__),
                             "resources",
                             "example_document_missing.txt"))
        output = papis.commands.main(args)

        self.assertTrue(output == status.file_not_found)

    def test_remove_missing(self):
        args = ("rm", "-f",
                "example_document_missing.txt")
        output = papis.commands.main(args)
        self.assertTrue(output != status.success)

    def test_add_file_with_dir(self):
        args = ("add", "--dir", "subdir",
                os.path.join(os.path.dirname(__file__),
                             "resources",
                             "example_document.txt"))
        output = papis.commands.main(args)

        self.assertTrue(output == status.success)

        args = ("rm", "-f", "example_document.txt")
        output = papis.commands.main(args)
        self.assertTrue(output == status.success)

        # Double removal fails
        args = ("rm", "-f", "example_document.txt")
        output = papis.commands.main(args)
        self.assertTrue(output == status.file_not_found)

    def test_add_file_with_file_name(self):
        args = ("add", "--file-name", "new_name",
                "--dir", "foldname",
                os.path.join(os.path.dirname(__file__),
                             "resources",
                             "example_document.txt"))

        doc_data = {'author': "Unknown"}
        cmd = papis.commands.add.Command()
        expected_folder_name = cmd.get_hash_folder(
            doc_data,
            os.path.join(
                os.path.dirname(__file__),
                "resources",
                "example_document.txt"))

        output = papis.commands.main(args)

        # The command has the result we expect
        self.assertTrue(output == status.success)

        lib_dir = os.path.expanduser(papis.config.get('dir'))
        out_dir = os.path.join(lib_dir, "foldname", expected_folder_name)
        # The folder is created
        self.assertTrue(os.path.isdir(out_dir))

        # The file is added
        self.assertTrue(os.path.isfile(os.path.join(out_dir, "new_name.txt")))
        # The content of the file is the one we'd expect
        self.assertTrue(files_are_equal(
            os.path.join(os.path.dirname(__file__),
                         "resources", "example_document.txt"),
            os.path.join(out_dir, "new_name.txt")))

        args = ("rm", "-f", expected_folder_name)
        output = papis.commands.main(args)
        self.assertTrue(output == status.success)

        # Doble removal fails
        args = ("rm", "-f", expected_folder_name)
        output = papis.commands.main(args)
        self.assertTrue(output == status.file_not_found)
