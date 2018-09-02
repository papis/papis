import papis.downloaders.utils
from papis.downloaders.acs import Downloader
import papis.bibtex


def test_match():
    assert(Downloader.match(
        'blah://pubs.acs.org/doi/abs/10.1021/acs.jchemed.6b00559'
    ))
    assert(Downloader.match(
        'blah://pubs.acs.org/!@#!@$!%!@%!$che.6b00559'
    ))
    assert(Downloader.match(
            'acs.com/!@#!@$!%!@%!$chemed.6b00559'
    ) is False)

def test_downloader_getter():
    url = 'https://pubs.acs.org/doi/abs/10.1021/ed044p128?src=recsys'
    down = papis.downloaders.utils.get_downloader(url)
    assert(down.expected_document_extension == 'pdf')
    assert(down.get_doi() == '10.1021/ed044p128')
    assert(len(down.get_bibtex_url()) > 0)
    assert(len(down.get_bibtex_data()) > 0)
    # bibs = papis.bibtex.bibtex_to_dict(down.get_bibtex_data())
    # assert(len(bibs) == 1)
    # doc = down.get_document_data()
    # assert(doc is not None)
    # assert(not down.check_document_format())

    # # this is an open access paper, so it should work
    # down = papis.downloaders.utils.get(
     # 'https://journals.down.org/prl/abstract/10.1103/PhysRevLett.121.091601'
    # )
    # assert(isinstance(down, dict))
    # assert(down.get('doi') is not None)
    # assert(down.get('doi') == down.get('data').get('doi'))
    # assert(down.get('data') is not None)
    # assert(isinstance(down.get('data'), dict))
    # assert(down.get('documents_paths') is not None)
    # assert(len(down.get('documents_paths')) == 1)
