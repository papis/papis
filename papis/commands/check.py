import papis
import os
import papis.utils


class Check(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "check",
            help="Check document document from a given library"
        )

        self.parser.add_argument(
            "document",
            help="Document search",
            nargs="?",
            default=".",
            action="store"
        )

        self.parser.add_argument(
            "--keys", "-k",
            help="Key to check",
            nargs="*",
            default=[],
            action="store"
        )

    def main(self):
        documentsDir = os.path.expanduser(self.get_config()[self.args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = self.args.document
        documents = papis.utils.get_documents_in_dir(
            documentsDir,
            documentSearch
        )
        allOk = True
        for document in documents:
            self.logger.debug("Checking %s" % document.get_main_folder())
            allOk &= document.check_files()
            for key in self.args.keys:
                if key not in document.keys():
                    allOk &= False
                    print(
                        "%s not found in %s" % (
                            key, document.get_main_folder()
                        )
                    )
        if not allOk:
            print("Errors were detected, please fix the info files")
        else:
            print("No errors detected")
