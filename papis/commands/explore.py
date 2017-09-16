import papis.utils
import papis.document
import papis.config
import papis.bibtex
import urllib.request


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
            "--arxiv",
            help="Search on the arxiv",
            action="store_true"
        )

        self.parser.add_argument(
            "--max",
            help="Maximum number of items",
            default=30,
            action="store"
        )

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
        self.pick(documents)

    def main(self):
        if self.args.arxiv:
            self.arxiv(self.args.search)
        else:
            self.arxiv(self.args.search)
