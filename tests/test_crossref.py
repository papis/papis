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


def test_get_clean_doi():
    assert(
        get_clean_doi('http://dx.doi.org/10.1063%2F1.881498') ==
        '10.1063/1.881498'
    )
    assert(
        get_clean_doi('http://dx.doi.org/10.1063/1.881498') ==
        '10.1063/1.881498'
    )
    assert(get_clean_doi('10.1063%2F1.881498') == '10.1063/1.881498')
    assert(get_clean_doi('10.1063/1.881498') == '10.1063/1.881498')
    assert(
        get_clean_doi(
            'http://physicstoday.scitation.org/doi/10.1063/1.uniau12/abstract'
        ) == '10.1063/1.uniau12'
    )
    assert(
        get_clean_doi(
            'http://scitation.org/doi/10.1063/1.uniau12/abstract?as=234'
        ) == '10.1063/1.uniau12'
    )
    assert(
        get_clean_doi(
            'http://physicstoday.scitation.org/doi/10.1063/1.881498'
        ) == '10.1063/1.881498'
    )
    assert(
        get_clean_doi(
            'https://doi.org/10.1093/analys/anw053' 
        ) == '10.1093/analys/anw053'
    )
    assert(
        get_clean_doi(
            'http://physicstoday.scitation.org/doi/10.1063/1.881498?asdfwer' 
        ) == '10.1063/1.881498'
    )
