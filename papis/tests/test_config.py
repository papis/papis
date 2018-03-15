import unittest
import logging
import papis.config
from papis.commands.config import run

logging.basicConfig(level=logging.DEBUG)


class TestCommand(unittest.TestCase):

    def test_simple(self):
        self.assertTrue(run('editor') == papis.config.get('editor'))
        self.assertTrue(run('xeditor') == papis.config.get('xeditor'))
        self.assertTrue(run('settings.xeditor') == papis.config.get('xeditor'))
        self.assertTrue(
            run('dmenu-gui.lines') ==
            papis.config.get('lines', section='dmenu-gui')
        )


class TestDefaultConfiguration(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        pass

    @classmethod
    def tearDownClass(self):
        pass

    def test_gui_default_config(self):
        """Test that the gui has a method to get default config
        """
        import papis.gui
        # Function exists
        self.assertTrue(papis.gui.get_default_settings)

        settings = papis.gui.get_default_settings()
        self.assertTrue(settings)

        self.assertTrue(isinstance(settings, dict))
        for section in ["vim-gui", "rofi-gui", "tk-gui"]:
            self.assertTrue(section in settings.keys())

    def test_default_config(self):
        """Test main default config
        """
        self.assertTrue(papis.config.get_default_settings)

        settings = papis.config.get_default_settings()
        self.assertTrue(settings)

        self.assertTrue(isinstance(settings, dict))
        for section in ["settings", "vim-gui", "rofi-gui", "tk-gui"]:
            self.assertTrue(section in settings.keys())
