import papis.downloaders.utils
from papis.downloaders.aps import Downloader
import papis.bibtex


def test_match():
    assert(Downloader.match(
        'blah://pubs.aps.org/doi/abs/10.1021/acs.jchemed.6b00559'
    ))
    assert(Downloader.match(
        'blah://pubs.aps.org/!@#!@$!%!@%!$che.6b00559'
    ))
    assert(Downloader.match(
        'aps.com/!@#!@$!%!@%!$chemed.6b00559'
    ) is False)


def test_downloader_getter():
    assert(papis.downloaders.utils.get_downloader is not None)
    aps = papis.downloaders.utils.get_downloader(
        "http://journals.aps.org/prb/abstract/10.1103/PhysRevB.95.085434"
    )
    assert(aps.expected_document_extension == 'pdf')
    assert(len(aps.get_bibtex_url()) > 0)
    assert(len(aps.get_bibtex_data()) > 0)
    bibs = papis.bibtex.bibtex_to_dict(aps.get_bibtex_data())
    assert(len(bibs) == 1)
    doc = aps.get_document_data()
    assert(doc is not None)
    assert(not aps.check_document_format())

    # this is an open access paper, so it should work
    aps = papis.downloaders.utils.get(
     'https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.091601'
    )
    assert(isinstance(aps, dict))
    assert(aps.get('doi') is not None)
    assert(aps.get('doi') == aps.get('data').get('doi'))
    assert(aps.get('data') is not None)
    assert(isinstance(aps.get('data'), dict))
    assert(aps.get('documents_paths') is not None)
    assert(len(aps.get('documents_paths')) == 1)
