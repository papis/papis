import papis.downloaders.utils
from papis.downloaders.annualreviews import Downloader
import papis.bibtex


def test_match():
    assert(Downloader.match(
        'http://anualreviews.org/doi/pdf/'
        '10.1146/annurev-conmatphys-031214-014726'
    ) is False)

    assert(Downloader.match(
        'http://annualreviews.org/doi/pdf/'
        '10.1146/annurev-conmatphys-031214-014726'
    ))

def test_downloader_getter():
    url = 'http://annualreviews.org/doi/pdf/'\
          '10.1146/annurev-conmatphys-031214-014726'\
          '?asdfasdf=23'
    down = papis.downloaders.utils.get_downloader(url)
    assert(down.name == 'annualreviews')
    assert(down.expected_document_extension == 'pdf')
    assert(down.get_doi() == '10.1146/annurev-conmatphys-031214-014726')
    assert(len(down.get_bibtex_url()) > 0)
    assert(len(down.get_bibtex_data()) > 0)
    bibs = papis.bibtex.bibtex_to_dict(down.get_bibtex_data())
    assert(len(bibs) == 1)
    doc = down.get_document_data()
    assert(doc is not None)
    assert(not down.check_document_format())
