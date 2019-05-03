import papis.downloaders
from papis.downloaders.iopscience import Downloader
import papis.bibtex


def test_match():
    assert(
        Downloader.match(
            'http://iopscience.iop.org/article/10.1088/0305-4470/24/2/004'
        )
    )
    assert(
        Downloader.match(
            'blah://iop.org/!@#!@$!%!@%!$che.6b00559'
        ) is False
    )
    assert(
        Downloader.match(
            'iopscience.iop.com/!@#!@$!%!@%!$chemed.6b00559'
        ) is False
    )
    down = Downloader.match(
        'http://iopscience.iop.org/article/10.1088/0305-4470/24/2/004/pdf?as=2'
    )
    assert(down)
    assert(down.get_doi() == '10.1088/0305-4470/24/2/004')
    assert(down._get_article_id() == '0305-4470/24/2/004')

def test_downloader_getter():
    url = 'http://iopscience.iop.org/article/10.1088/0305-4470/24/2/004?a=2'
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'iopscience')
    assert(down.expected_document_extension == 'pdf')
    assert(down.get_doi() == '10.1088/0305-4470/24/2/004')
    assert(len(down.get_bibtex_url()) > 0)
    assert(len(down.get_bibtex_data()) > 0)
    bibs = papis.bibtex.bibtex_to_dict(down.get_bibtex_data())
    assert(len(bibs) == 1)
    doc = down.get_document_data()
    assert(doc is not None)
    # not open access
    # TODO:
    # assert(not down.check_document_format())
