import papis.utils
import papis.commands
import papis.document
import papis.config
import papis.bibtex
import urllib.request
import tempfile


class Command(papis.commands.Command):

    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "explore",
            help="Explore on the internet"
        )

        self.parser.add_argument(
            "search",
            help="Search string",
            default=[],
            nargs="*",
            action="store"
        )

        self.parser.add_argument(
            "--isbnplus",
            help="Search through isbnplus.org",
            action="store_true"
        )

        self.parser.add_argument(
            "--arxiv",
            help="Search on the arxiv",
            action="store_true"
        )

        self.parser.add_argument(
            "--libgen",
            help="Search on library genesis",
            action="store_true"
        )

        self.parser.add_argument(
            "--add",
            help="Add document selected",
            action="store_true"
        )

        self.parser.add_argument(
            "--max",
            help="Maximum number of items",
            default=30,
            action="store"
        )

    def add(self, doc):
        if self.args.libgen:
            if not 'doc_url' in doc.keys():
                self.logger.error('No doc_url data retrieved')
                return 1
            self.logger.info('Downloading document')
            doc_data = urllib.request.urlopen(
                doc['doc_url']
            ).read()
            file_name = tempfile.mktemp()
            with open(file_name, 'wb+') as fd:
                fd.write(doc_data)
            papis.commands.main(
                ['add', '--from-url', doc['doc_url'], file_name]
            )
        elif self.args.arxiv:
            if not 'url' in doc.keys():
                self.logger.error('No url data retrieved')
                return 1
            papis.commands.main(
                ['add', '--from-url', doc['url']]
            )

    def libgen(self, search):
        from pylibgen import Library
        lg = Library()
        ids = lg.search(ascii(search), 'title')
        data = lg.lookup(ids)
        doc = self.pick(
            [papis.document.Document(data=d) for d in data]
        )
        if doc:
            doc['doc_url'] = lg.get_download_url(doc['md5'])
        return doc

    def isbnplus(self, search):
        import papis.isbn
        data = papis.isbn.get_data(query=search)
        doc = self.pick(
            [papis.document.Document(data=d) for d in data]
        )
        return doc

    def arxiv(self, search):
        # FIXME: use a more lightweight library than bs4, it needs some time
        # to import the module
        import bs4
        main_url = "http://export.arxiv.org/api/query?search_query="
        url = main_url+"all:{}&max_results={}".format(
            "%20".join(search),
            self.args.max
        )
        self.logger.debug("Url = %s" % url)
        raw_data = urllib.request.urlopen(url).read().decode('utf-8')
        soup = bs4.BeautifulSoup(raw_data, "html.parser")
        entries = soup.find_all("entry")
        self.logger.debug("%s matches" % len(entries))
        documents = []
        for entry in entries:
            data = dict()
            data["abstract"] = entry.find("summary").get_text().replace(
                "\n", " "
            )
            data["url"] = entry.find("id").get_text()
            data["year"] = entry.find("published").get_text()[0:4]
            data["title"] = entry.find("title").get_text().replace("\n", " ")
            data["author"] = ", ".join(
                [
                    author.get_text().replace("\n", "")
                    for author in entry.find_all("author")
                ]
            )
            document = papis.document.Document(data=data)
            documents.append(document)
        doc = self.pick(documents)
        return doc

    def main(self):
        doc = None
        if self.args.arxiv:
            doc = self.arxiv(self.args.search)
        elif self.args.isbnplus:
            doc = self.isbnplus(self.args.search)
        elif self.args.libgen:
            doc = self.libgen(self.args.search)
        else:
            doc = self.arxiv(self.args.search)

        if doc:
            print(doc.dump())
            if self.args.add:
                self.add(doc)
