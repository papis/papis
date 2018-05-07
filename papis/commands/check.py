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

    papis check --keys files author title
"""
import papis.api
import papis.config


def run(keys, documents):
    result = []
    for document in documents:
        for key in keys:
            if key not in document.keys():
                result.append(
                    dict(doc=document, key=key, msg='not defined')
                )
            elif not document[key] and document[key] is not False:
                result.append(
                    dict(doc=document, key=key, msg='ill defined')
                )
            elif key == 'files':
                if not document.check_files():
                    result.append(
                        dict(doc=document, key=key, msg='problem with files')
                    )
    return result


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "check",
            help="Check document from a given library"
        )

        self.add_search_argument()

        self.parser.add_argument(
            "--keys", "-k",
            help="Space separated fields to check against",
            nargs='*',
            default=eval(papis.config.get('check-keys')),
            action="store"
        )

    def main(self):
        documents = self.get_db().query(self.args.search)
        self.logger.debug(self.args.keys)
        troubled_docs = run(self.args.keys, documents)
        for doc in troubled_docs:
            print(
                "{d[key]} - {d[msg]} - {folder}".format(
                    d=doc, folder=doc['doc'].get_main_folder()
                )
            )

        if not len(troubled_docs) == 0:
            print("Errors were detected, please fix the info files")
        else:
            print("No errors detected")
