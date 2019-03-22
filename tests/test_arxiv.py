from papis.arxiv import *

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
