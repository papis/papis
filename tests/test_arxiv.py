import papis.downloaders
from papis.arxiv import Downloader, get_data, find_arxivid_in_text
import papis.bibtex

def test_general():
    data = get_data(
        author='Garnet Chan',
        max_results=1,
        title='Finite Temperature'
    )
    assert(data)
    assert(len(data) == 1)


def test_find_arxiv_id():
    test_data = [
        ('/URI(http://arxiv.org/abs/1305.2291v2)>>', '1305.2291v2'),
        ('/URI(http://arxiv.org/abs/1205.0093)>>', '1205.0093'),
        ('/URI(http://arxiv.org/abs/1205.1494)>>', '1205.1494'),
        ('/URI(http://arxiv.org/abs/1011.2840)>>', '1011.2840'),
        ('/URI(http://arxiv.org/abs/1110.3658)>>', '1110.3658'),
        ('http://arxiv.org/abs/1110.3658>', '1110.3658'),
        ('http://arxiv.com/abs/1110.3658>', '1110.3658'),
        ('http://arxiv.org/1110.3658>', '1110.3658'),
    ]
    for url, arxivid in test_data:
        assert(find_arxivid_in_text(url) == arxivid)


def test_match():
    assert(Downloader.match('arxiv.org/sdf'))
    assert(Downloader.match('arxiv.com/!@#!@$!%!@%!$chemed.6b00559') is False)

    down = Downloader.match('arXiv:1701.08223v2?234')
    assert(down)
    assert(down.get_url() == 'https://arxiv.org/abs/1701.08223v2')
    assert(down.get_identifier() == '1701.08223v2')


def test_downloader_getter():
    url = 'https://arxiv.org/abs/1001.3032'
    down = papis.downloaders.get_downloader(url)
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
