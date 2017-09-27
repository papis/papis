"""
This command checks for several attributes in every document.

For example if you want to chekc that every document of your library has valid
files related to it you can just do

::

    papis check --keys files

this will check that every info file has the key files and that every file
listed exists.

You can also define your own ones by inputing comma separated keys, e.g. if you
want to check that every document has files, a valid author and title you would
just hut

::

    papis check --keys files,author,title
"""
import papis.api
import papis.config


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "check",
            help="Check document from a given library"
        )

        self.add_search_argument()

        self.parser.add_argument(
            "--keys", "-k",
            help="Comma separated keys to check",
            default=papis.config.get('check-keys'),
            action="store"
        )

    def main(self):
        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
        )
        all_ok = True
        doc_ok = True
        self.args.keys = self.args.keys.split(',')
        self.logger.debug(self.args.keys)
        for document in documents:
            doc_ok = True
            for key in self.args.keys:
                if key not in document.keys():
                    all_ok &= False
                    doc_ok &= False
                    print(
                        "%s not found in %s" % (
                            key, document.get_main_folder()
                        )
                    )
                elif not document[key] and document[key] is not False:
                    all_ok &= False
                    print(
                        "%s is ill-defined (%s) in %s" % (
                            key, document[key], document.get_main_folder()
                        )
                    )
                elif key == 'files':
                    all_ok &= document.check_files()
        if not all_ok:
            print("Errors were detected, please fix the info files")
        else:
            print("No errors detected")
