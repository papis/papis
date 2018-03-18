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
            default="",
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
            "--crossref",
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

        self.parser.add_argument(
            "--cmd",
            help="Issue a command on the retrieved document "
                 "using papis format",
            default=None,
            action="store"
        )

    def parse_search(self):
        import papis.docmatcher
        key_vals = papis.docmatcher.parse_query(self.args.search)
        result = {'query': ""}
        self.logger.debug('Parsed set %s' % key_vals)
        for pair in key_vals:
            if len(pair) == 3:
                key = pair[0]
                val = pair[2]
                result[key] = val
            else:
                val = pair[0]
                result['query'] += ' ' + val
        return result

    def add(self, doc):
        if self.args.libgen:
            if not doc.has('doc_url'):
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
            if not doc.has('url'):
                self.logger.error('No url data retrieved')
                return 1
            papis.commands.main(
                ['add', '--from-url', doc['url']]
            )

    def libgen(self, search):
        from pylibgen import Library
        parsed = self.parse_search()
        lg = Library()
        ids = []
        for key in ['title', 'author', 'isbn']:
            if parsed.get(key):
                ids += lg.search(ascii(parsed.get(key)), key)
        if len(ids) == 0:
            ids = lg.search(ascii(parsed.get('query')), 'title')
        if len(ids):
            data = lg.lookup(ids)
        else:
            self.logger.error("No documents found")
            return None
        doc = self.pick(
            [papis.document.Document(data=d) for d in data]
        )
        if doc:
            doc['doc_url'] = lg.get_download_url(doc['md5'])
        return doc

    def crossref(self, search):
        import papis.crossref
        parsed = self.parse_search()
        data = papis.crossref.get_data(
            query=parsed.get('query'),
            author=parsed.get('author'),
            title=parsed.get('title'),
            year=parsed.get('year'),
            max_results=self.args.max
        )
        documents = [papis.document.Document(data=d) for d in data]
        doc = self.pick(
            documents
        )
        return doc

    def isbnplus(self, search):
        import papis.isbn
        data = papis.isbn.get_data(query=search)
        doc = self.pick(
            [papis.document.Document(data=d) for d in data]
        )
        return doc

    def arxiv(self, search):
        import papis.arxiv
        parsed = self.parse_search()
        data = papis.arxiv.get_data(
            query=parsed.get('query'),
            author=parsed.get('author'),
            title=parsed.get('title'),
            abstract=parsed.get('abstract'),
            comment=parsed.get('comment'),
            journal=parsed.get('journal'),
            report_number=parsed.get('report_number'),
            category=parsed.get('category'),
            id_list=parsed.get('id_list'),
            page=parsed.get('page') or 0,
            max_results=self.args.max
        )
        doc = self.pick(
            [papis.document.Document(data=d) for d in data]
        )
        return doc

    def main(self):
        doc = None
        if self.args.arxiv:
            doc = self.arxiv(self.args.search)
        elif self.args.isbnplus:
            doc = self.isbnplus(self.args.search)
        elif self.args.crossref:
            doc = self.crossref(self.args.search)
        elif self.args.libgen:
            doc = self.libgen(self.args.search)
        else:
            self.args.arxiv = True
            doc = self.arxiv(self.args.search)

        if doc:
            print(papis.document.dump(doc))
            if self.args.add:
                self.add(doc)
            elif self.args.cmd is not None:
                from subprocess import call
                command = papis.utils.format_doc(
                    self.args.cmd,
                    doc
                )
                self.logger.debug('Calling "%s"' % command)
                call(command.split(" "))
