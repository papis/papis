from ..document import Document
import papis
import sys
import os
import papis.utils
from . import Command


class Test(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        # test parser
        test_parser = parser.add_parser("test",
                help="For testing (ignore)")

    def main(self, config, args):
        """
        Main action if the command is triggered

        :config: User configuration
        :args: CLI user arguments
        :returns: TODO

        """
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        self.logger.debug("Using directory %s"%documentsDir)
        papis.utils.pickFile(["1","3"], config)
