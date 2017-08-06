import papis
import os
import papis.utils


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "check",
            help="Check document document from a given library"
        )

        self.add_search_argument()

        self.parser.add_argument(
            "--keys", "-k",
            help="Key to check",
            nargs="*",
            default=[],
            action="store"
        )

    def main(self):
        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
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
