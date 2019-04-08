"""The following table lists the field prefixes for all the fields
 that can be searched.

 Table:          search_query field prefixes
============================================
 prefix          explanation
--------------------------------------------
 ti              Title
 au              Author
 abs             Abstract
 co              Comment
 jr              Journal Reference
 cat             Subject Category
 rn              Report Number
 id              Id (use id_list instead)
 all             All of the above
"""
import bs4
import logging
import urllib.request  # urlopen, Request
import urllib.parse  # import urlencode
import papis.config
import re
import click
import papis.downloaders.base
import arxiv2bib


logger = logging.getLogger('arxiv')


def get_data(
    query="",
    author="",
    title="",
    abstract="",
    comment="",
    journal="",
    report_number="",
    category="",
    id_list="",
    page=0,
    max_results=30
):
    dict_params = {
        "all": query,
        "ti": title,
        "au": author,
        "cat": category,
        "abs": abstract,
        "co": comment,
        "jr": journal,
        "id_list": id_list,
        "rn": report_number
    }
    result = []
    clean_params = {x: dict_params[x] for x in dict_params if dict_params[x]}
    search_query = '+AND+'.join(
        [key+':'+str(clean_params[key]) for key in clean_params]
    )
    logger.debug("query = " + search_query)
    params = urllib.parse.urlencode(
        {
            'search_query': search_query,
            'start': page,
            'max_results': max_results
        }
    )
    main_url = "http://arxiv.org/api/query?"
    req_url = main_url + params
    logger.debug("url = " + req_url)
    url = urllib.request.Request(
        req_url,
        headers={
            'User-Agent': papis.config.get('user-agent')
        }
    )
    xmldoc = urllib.request.urlopen(url).read()
    soup = bs4.BeautifulSoup(xmldoc, 'html.parser')

    entries = soup.find_all("entry")
    for entry in entries:
        data = dict()
        data["abstract"] = entry.find("summary").get_text().replace(
            "\n", " "
        )
        data["url"] = entry.find("id").get_text()
        data["published"] = entry.find("published").get_text()
        data["year"] = data.get("published")[0:4]
        data["title"] = entry.find("title").get_text().replace("\n", " ")
        data["author"] = ", ".join(
            [
                author.get_text().replace("\n", "")
                for author in entry.find_all("author")
            ]
        )
        result.append(data)
    return result


def pdf_to_arxivid(filepath):
    """Try to get arxivid from a filepath, it looks for a regex in the binary
    data and returns the first arxivid found, in the hopes that this arxivid
    is the correct one.

    :param filepath: Path to the pdf file
    :type  filepath: str
    :returns: arxivid or None
    :rtype:  str or None
    """
    arxivid = None
    with open(filepath, 'rb') as fd:
        for line in fd:
            arxivid = find_arxivid_in_text(
                line.decode('ascii', errors='ignore')
            )
            if arxivid:
                break
    return arxivid


def find_arxivid_in_text(text):
    """
    Try to find a arxivid in a text
    """
    forbidden_arxivid_characters = r'"\(\)\s%!$^\'<>@,;:#?&'
    # Sometimes it is in the javascript defined
    regex = re.compile(
        r'arxiv(.org|.com)?'
        r'(/abs|/pdf)?'
        r'\s*(=|:|/|\()\s*'
        r'("|\')?'
        r'(?P<arxivid>[^{fc}]+)'
        r'("|\'|\))?'
        .format(
            fc=forbidden_arxivid_characters
        ), re.I
    )
    miter = regex.finditer(text)
    try:
        m = next(miter)
        if m:
            arxivid = m.group('arxivid')
            return arxivid
    except StopIteration:
        pass
    return None


@click.command('arxiv')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--query', '-q', default=None)
@click.option('--author', '-a', default=None)
@click.option('--title', '-t', default=None)
@click.option('--abstract', default=None)
@click.option('--comment', default=None)
@click.option('--journal', default=None)
@click.option('--report-number', default=None)
@click.option('--category', default=None)
@click.option('--id-list', default=None)
@click.option('--page', default=None)
@click.option('--max', '-m', default=20)
def explorer(ctx, query, author, title, abstract, comment,
             journal, report_number, category, id_list, page, max):
    """
    Look for documents on ArXiV.org.

    Examples of its usage are

        papis explore arxiv -a 'Hummel' -m 100 arxiv -a 'Garnet Chan' pick

    If you want to search for the exact author name 'John Smith', you should
    enclose it in extra quotes, as in the example below

        papis explore arxiv -a '"John Smith"' pick

    """
    logger = logging.getLogger('explore:arxiv')
    logger.info('Looking up...')
    data = get_data(
        query=query,
        author=author,
        title=title,
        abstract=abstract,
        comment=comment,
        journal=journal,
        report_number=report_number,
        category=category,
        id_list=id_list,
        page=page or 0,
        max_results=max
    )
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, uri=url, name="arxiv")
        self.expected_document_extension = 'pdf'
        self.arxivid = None

    @classmethod
    def match(cls, url):
        arxivid = find_arxivid_in_text(url)
        if arxivid:
            url = "https://arxiv.org/abs/{0}".format(arxivid)
            down = Downloader(url)
            down.arxivid = arxivid
            return down
        else:
            return False

    def _get_identifier(self):
        """Get arxiv identifier
        :returns: Identifier
        """
        if not self.arxivid:
            self.arxivid = find_arxivid_in_text(self.uri)
        return self.arxivid

    def get_bibtex_url(self):
        identifier = self._get_identifier()
        return identifier

    def download_bibtex(self):
        bib_url = self.get_bibtex_url()
        bibtexCli = arxiv2bib.Cli([bib_url])
        bibtexCli.run()
        self.logger.debug("[bibtex url] = %s" % bib_url)
        data = ''.join(bibtexCli.output).replace('\n', ' ')
        self.bibtex_data = data

    def get_document_url(self):
        arxivid = self._get_identifier()
        self.logger.debug("arxivid %s" % arxivid)
        pdf_url = "https://arxiv.org/pdf/{arxivid}.pdf".format(arxivid=arxivid)
        self.logger.debug("[pdf url] = %s" % pdf_url)
        return pdf_url


class Importer(papis.importer.Importer):

    def __init__(self, uri='', **kwargs):
        papis.importer.Importer.__init__(self, name='arxiv', uri=uri, **kwargs)
        self.downloader = Downloader('https://arxiv.org/abs/{0}'.format(uri))

    def fetch(self):
        self.downloader.fetch()
        self.ctx = self.downloader.ctx
