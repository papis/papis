import papis.downloaders.utils
from papis.downloaders.arxiv import Downloader
import papis.bibtex


def test_match():
    assert(Downloader.match('arxiv.org/sdf'))
    assert(Downloader.match('arxiv.com/!@#!@$!%!@%!$chemed.6b00559') is False)

    down = Downloader.match('arXiv:1701.08223v2?234')
    assert(down)
    assert(down.get_url() == 'https://arxiv.org/abs/1701.08223v2')
    assert(down.get_identifier() == '1701.08223v2')


def test_downloader_getter():
    url = 'https://arxiv.org/abs/1001.3032'
    down = papis.downloaders.utils.get_downloader(url)
    assert(down.name == 'arxiv')
    assert(down.expected_document_extension == 'pdf')
    #assert(down.get_doi() == '10.1021/ed044p128')
    assert(len(down.get_bibtex_url()) > 0)
    assert(len(down.get_bibtex_data()) > 0)
    bibs = papis.bibtex.bibtex_to_dict(down.get_bibtex_data())
    assert(len(bibs) == 1)
    doc = down.get_document_data()
    assert(doc is not None)
    assert(down.check_document_format())
