import os
import subprocess
import tempfile
import logging


class Gui(object):

    def __init__(self):
        self.documents = []
        self.logger = logging.getLogger("gui:vim")
        self.main_vim_path = os.path.join(
            os.path.dirname(__file__),
            "main.vim"
        )

    def main(self, documents):
        temp_file = tempfile.mktemp()
        self.logger.debug("Temp file = %s" % temp_file)

        fd = open(temp_file, "w+")
        for doc in documents:
            fd.write(doc["title"] + "\n")
        fd.close()

        subprocess.call(
                ["vim", "-S", self.main_vim_path, "-R", temp_file]
        )
