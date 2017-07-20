import unittest

class TestTk(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_import_tk(self):
        try:
            import papis.gui.tk
        except:
            self.assertFalse(True)
