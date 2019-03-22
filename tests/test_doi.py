from papis.doi import *


def test_validate_doi():
    doi = '10.1063/1.5081715'
    validate_doi(doi)
    for doi in ['', 'asdf']:
        try:
            validate_doi(doi)
        except ValueError as e:
            assert(str(e) == 'HTTP 404: DOI not found')


# def test_get_clean_doi():
    # test_data = [
        # ('http://dx.doi.org/10.1063%2F1.881498', '10.1063/1.881498'),
        # ('http://dx.doi.org/10.1063/1.881498', '10.1063/1.881498'),
        # ('http://physicstoday.scitation.org/doi/10.1063/1.uniau12/abstract',
            # '10.1063/1.uniau12'),
        # ('http://scitation.org/doi/10.1063/1.uniau12/abstract?as=234',
            # '10.1063/1.uniau12'),
        # ('http://physicstoday.scitation.org/doi/10.1063/1.881498',
            # '10.1063/1.881498'),
        # ('https://doi.org/10.1093/analys/anw053' , '10.1093/analys/anw053'),
        # ('http://.scitation.org/doi/10.1063/1.881498?asdfwer' ,
            # '10.1063/1.881498'),
    # ]
    # for url, doi in test_data:
        # assert(get_clean_doi(url) == doi)


def test_find_doi_in_line():
    test_data = [
        ('10.1063/1.881498', '10.1063/1.881498'),
        ('http://dx.doi.org/10.1063/1.881498', '10.1063/1.881498'),
        ('http://dx.doi.org/10.1063%2F1.881498', '10.1063/1.881498'),
        (2*'qer '+'var doi = "12345/12345.3"', '12345/12345.3'),
        (2*'qer '+"var doi = '12345/12345.3';fas", '12345/12345.3'),
        (2*'qer '+"var DoI = 12345%2F12345.3", '12345/12345.3'),
        (2*'qer '+"var DoI : 12345%2F12345.3", '12345/12345.3'),
        ('http://scitation.org/doi/10.1063/1.881498', '10.1063/1.881498'),
        ('org/doi(10.1063/1.881498)', '10.1063/1.881498)'),
        ('/scitation.org/doi/10.1063/1.881498?234saf=34', '10.1063/1.881498'),
        ('/scitation.org/doi/10.1063/1.88149 8?234saf=34', '10.1063/1.88149'),
        ('/scitation.org/doi/10.1063/1.uniau12?as=234',
            '10.1063/1.uniau12'),
        ('https://doi.org/10.1093/analys/anw053' , '10.1093/analys/anw053'),
        ('http://.scitation.org/doi/10.1063/1.mart(88)1498?asdfwer' ,
            '10.1063/1.mart(88)1498'),
        ('@ibook{doi:10.1002/9780470125915.ch2,', '10.1002/9780470125915.ch2'),
        ('<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1'
         '.1/"><dc:format>application/pdf</dc:format><dc:identifier>'
         'doi:10.1063/1.5079474</dc:identifier></rdf:Description>',
            '10.1063/1.5079474'),
        ('<(DOI:10.1002/9780470915.CH2)/S/URI,', '10.1002/9780470915.CH2'),
        ('URL<(DOI:10.1002/9780470125915.CH2,', '10.1002/9780470125915.CH2'),
        (r'A<</S/URI/URI(https://doi.org/10.1016/j.comptc.2018.10.004)>>/'
         r'Border[0 0 0]/M(D:20181022082356+0530)/Rect[147.40158 594.36926'
         r'347.24957 605.36926]/Subtype/Link/Type/A',
            '10.1016/j.comptc.2018.10.004'),
        ('doi(10.1038/s41535-018-0103-6;)', '10.1038/s41535-018-0103-6'),
    ]
    for url, doi in test_data:
        assert(find_doi_in_text(url) == doi)


