import os
import unittest
import logging
import papis.config
from papis.commands.config import run

logging.basicConfig(level=logging.DEBUG)


class TestCommand(unittest.TestCase):

    def test_simple(self):
        self.assertEqual(run("editor"), papis.config.get("editor"))
        self.assertEqual(run("settings.editor"), papis.config.get("editor"))
        self.assertEqual(run("papers.dir"), papis.config.get("dir", section="papers"))


class TestDefaultConfiguration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_default_config(self):
        """Test main default config
        """
        self.assertTrue(papis.config.get_default_settings)

        settings = papis.config.get_default_settings()
        self.assertTrue(settings)

        self.assertIsInstance(settings, dict)
        for section in ["settings"]:
            self.assertIn(section, settings.keys())

    def test_set_lib(self):
        try:
            lib = "non-existing-library"
            self.assertFalse(os.path.exists(lib))
            papis.config.set_lib(lib)
        except Exception:
            self.assertTrue(True)
        else:
            self.assertTrue(False)
