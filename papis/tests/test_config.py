import unittest
import logging
import papis.config
import os


logging.basicConfig(level=logging.DEBUG)


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

        self.assertTrue(
            isinstance(
                papis.config.get_default_settings(key="mode"),
                str
            )
        )

        self.assertTrue(
            isinstance(
                papis.config.get_default_settings(
                    section=papis.config.get_general_settings_name(),
                    key="mode"
                ),
                str
            )
        )

        self.assertTrue(isinstance(settings, dict))
        for section in ["settings", "vim-gui", "rofi-gui", "tk-gui"]:
            self.assertTrue(section in settings.keys())
