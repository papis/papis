from papis.crossref import (
    get_data, get_clean_doi, doi_to_data
)


def test_get_data():
    data = get_data(
        author='Albert Einstein',
        max_results=1,
    )
    assert(data)
    assert(len(data) == 1)


def test_doi_to_data():
    data = doi_to_data('http://dx.doi.org/10.1063%2F1.881498')
    assert(isinstance(data, dict))
    assert(data['doi'] == '10.1063/1.881498')
