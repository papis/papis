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
import os
import re
import logging
from typing import Optional, List, Dict, Any

import click

import papis.filetype
import papis.downloaders.base
import papis.config


logger = logging.getLogger('arxiv')


def get_data(
    query: str = "",
    author: str = "",
    title: str = "",
    abstract: str = "",
    comment: str = "",
    journal: str = "",
    report_number: str = "",
    category: str = "",
    id_list: str = "",
    page: int = 0,
    max_results: int = 30
        ) -> List[Dict[str, Any]]:
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
    logger.debug("query = '%s'", search_query)

    import urllib.parse
    params = urllib.parse.urlencode(
        {
            'search_query': search_query,
            'start': page,
            'max_results': max_results
        }
    )
    main_url = "http://arxiv.org/api/query?"
    req_url = main_url + params
    logger.debug("url = '%s'", req_url)

    import urllib.request
    url = urllib.request.Request(
        req_url,
        headers={
            'User-Agent': papis.config.getstring('user-agent')
        }
    )
    xmldoc = urllib.request.urlopen(url).read()

    import bs4
    soup = bs4.BeautifulSoup(xmldoc, 'html.parser')

    entries = soup.find_all("entry")
    for entry in entries:
        data = dict()
        data["abstract"] = entry.find("summary").get_text().replace(
            "\n", " "
        )
        data["url"] = entry.find("id").get_text()
        data["published"] = entry.find("published").get_text()
        published = data.get("published")
        if published:
            assert(isinstance(published, str))
            data["year"] = published[0:4]
        data["title"] = entry.find("title").get_text().replace("\n", " ")
        data["author"] = ", ".join(
            [
                author.get_text().replace("\n", "")
                for author in entry.find_all("author")
            ]
        )
        result.append(data)
    return result


def validate_arxivid(arxivid: str) -> None:
    import urllib.request
    url = "https://arxiv.org/abs/{0}".format(arxivid)
    request = urllib.request.Request(url)

    from urllib.error import HTTPError, URLError
    try:
        urllib.request.urlopen(request)
    except HTTPError:
        raise ValueError('HTTP 404: {0} not an arxivid'.format(arxivid))
    except URLError:
        pass


def pdf_to_arxivid(
        filepath: str, maxlines: float = float('inf')) -> Optional[str]:
    """Try to get arxivid from a filepath, it looks for a regex in the binary
    data and returns the first arxivid found, in the hopes that this arxivid
    is the correct one.

    :param filepath: Path to the pdf file
    :type  filepath: str
    :param maxlines: Maximum number of lines that should be checked
        For some documnets, it would spend a long time trying to look for
        a arxivid, and arxivids in the middle of documents don't tend to be the
        correct arxivid of the document.
    :type  maxlines: int
    :returns: arxivid or None
    :rtype:  str or None
    """
    with open(filepath, 'rb') as fd:
        for j, line in enumerate(fd):
            arxivid = find_arxivid_in_text(
                line.decode('ascii', errors='ignore'))
            if arxivid:
                return arxivid
            if j > maxlines:
                return None
    return None


def find_arxivid_in_text(text: str) -> Optional[str]:
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
@click.option('--query', '-q', default="", type=str)
@click.option('--author', '-a', default="", type=str)
@click.option('--title', '-t', default="", type=str)
@click.option('--abstract', default="", type=str)
@click.option('--comment', default="", type=str)
@click.option('--journal', default="", type=str)
@click.option('--report-number', default="", type=str)
@click.option('--category', default="", type=str)
@click.option('--id-list', default="", type=str)
@click.option('--page', default=0, type=int)
@click.option('--max', '-m', default=20, type=int)
def explorer(
        ctx: click.core.Context,
        query: str, author: str, title: str, abstract: str, comment: str,
        journal: str, report_number: str, category: str, id_list: str,
        page: int, max: int) -> None:
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
        max_results=max)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj['documents'] += docs

    logger.info('%s documents found', len(docs))


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str):
        papis.downloaders.Downloader.__init__(self, uri=url, name="arxiv")
        self.expected_document_extension = 'pdf'
        self.arxivid = None  # type: Optional[str]

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        arxivid = find_arxivid_in_text(url)
        if arxivid:
            url = "https://arxiv.org/abs/{0}".format(arxivid)
            down = Downloader(url)
            down.arxivid = arxivid
            return down
        else:
            return None

    def _get_identifier(self) -> Optional[str]:
        """Get arxiv identifier
        :returns: Identifier
        """
        if not self.arxivid:
            self.arxivid = find_arxivid_in_text(self.uri)
        return self.arxivid

    def get_bibtex_url(self) -> Optional[str]:
        return self._get_identifier()

    def download_bibtex(self) -> None:
        bib_url = self.get_bibtex_url()
        if not bib_url:
            return None

        import arxiv2bib
        bibtex_cli = arxiv2bib.Cli([bib_url])
        bibtex_cli.run()

        self.logger.debug("bibtex_url = '%s'", bib_url)
        output = bibtex_cli.output  # List[str]
        data = ''.join(output).replace('\n', ' ')
        self.bibtex_data = data

    def get_document_url(self) -> Optional[str]:
        arxivid = self._get_identifier()
        self.logger.debug("arxivid = '%s'", arxivid)
        pdf_url = "https://arxiv.org/pdf/{arxivid}.pdf".format(arxivid=arxivid)
        self.logger.debug("pdf_url = '%s'", pdf_url)
        return pdf_url


class Importer(papis.importer.Importer):

    """Importer accepting an arxiv id and downloading files and data"""

    def __init__(self, uri: str):
        papis.importer.Importer.__init__(self, name='arxiv', uri=uri)
        aid = find_arxivid_in_text(uri)
        self.downloader = Downloader('https://arxiv.org/abs/{0}'.format(aid))

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        try:
            validate_arxivid(uri)
        except ValueError:
            return None
        else:
            return Importer(uri=uri)

    def fetch(self) -> None:
        self.downloader.fetch()
        self.ctx = self.downloader.ctx


class ArxividFromPdfImporter(papis.importer.Importer):

    """Importer parsing an arxivid from a pdf file"""

    def __init__(self, uri: str):
        papis.importer.Importer.__init__(self, name='pdf2arxivid', uri=uri)
        self.arxivid = None  # type: Optional[str]

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        if (os.path.isdir(uri) or not os.path.exists(uri)
                or not papis.filetype.get_document_extension(uri) == 'pdf'):
            return None
        importer = ArxividFromPdfImporter(uri=uri)
        importer.arxivid = pdf_to_arxivid(uri, maxlines=2000)
        return importer if importer.arxivid else None

    def fetch(self) -> None:
        self.logger.info("Trying to parse arxivid from file '%s'", self.uri)
        if not self.arxivid:
            self.arxivid = pdf_to_arxivid(self.uri, maxlines=2000)
        if self.arxivid:
            self.logger.info("Parsed arxivid '%s'", self.arxivid)
            self.logger.warning(
                    "There is no guarantee that this arxivid is the one")
            importer = Importer.match(self.arxivid)
            if importer:
                importer.fetch()
                self.ctx = importer.ctx
