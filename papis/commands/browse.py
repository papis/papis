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
import os
import sys
import papis.utils
import papis.config


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "browse",
            help="Open document's url in a browser"
        )

        self.add_search_argument()

    def main(self):
        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
        )
        document = self.pick(documents)
        if not document: return 0

        url = None
        if "url" in document.keys():
            url = document["url"]
        elif 'doi' in document.keys():
            url = 'https://doi.org/' + document['doi']
        elif papis.config.get('doc-url-key-name') in document.keys():
            url = document[papis.config.get('doc-url-key-name')]
        else:
            from urllib.parse import urlencode
            params = {
                'q': papis.utils.format_doc(
                    papis.config.get('browse-query-format'),
                    document
                )
            }
            url = papis.config.get('search-engine') + '/?' + urlencode(params)


        if url is None:
            self.logger.warning(
                "No url for %s possible" % (document.get_main_folder_name())
            )
        else:
            self.logger.debug("Opening url %s:" % url)
            papis.utils.general_open(
                url, "browser"
            )
