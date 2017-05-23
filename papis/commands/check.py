import papis
import os
import papis.utils
from . import Command


class Check(Command):
    def init(self):
        self.subparser = self.parser.add_parser(
            "check",
            help="Check document document from a given library"
        )
        self.subparser.add_argument(
            "document",
            help="Document search",
            nargs="?",
            default=".",
            action="store"
        )
        self.subparser.add_argument(
            "--keys", "-k",
            help="Key to check",
            nargs="*",
            default=[],
            action="store"
        )

    def main(self, args):
        documentsDir = os.path.expanduser(self.config[args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        documents = papis.utils.get_documents_in_dir(
            documentsDir,
            documentSearch
        )
        allOk = True
        for document in documents:
            self.logger.debug("Checking %s" % document.getMainFolder())
            allOk &= document.checkFile()
            for key in args.keys:
                if key not in document.keys():
                    allOk &= False
                    print(
                        "%s not found in %s" % (key, document.getMainFolder())
                    )
        if not allOk:
            print("Errors were detected, please fix the info files")
        else:
            print("No errors detected")
