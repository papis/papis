from ..document import Document
import papis
import sys
import os
import papis.utils
from . import Command


class Sync(Command):
    def init(self):
        parser = self.parser.add_parser("sync",
                help="Sync a library using the sync command")

    def main(self, config, args):
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
