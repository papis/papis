"""This command will try its best to find a source in the internet for the
document at hand.

Of course if the document has an url key in its info file, it will use this url
to open it in a browser.  Also if it has a doc_url key, or a doi, it will try
to compose urls out of these to open it.

If none of the above work, then it will try to use a search engine with the
document's information (using the ``browse-query-format``).  You can select
wich search engine you want to use using the ``search-engine`` setting.

"""
import papis
import papis.utils
import papis.config
from papis.api import status


def run(document):
    papis.document.open_in_browser(document)
    return status.success


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "browse",
            help="Open document's url in a browser"
        )

        self.add_search_argument()

    def main(self):
        documents = self.get_db().query(self.args.search)
        document = self.pick(documents)
        if not document:
            return status.file_not_found
        return run(document)
