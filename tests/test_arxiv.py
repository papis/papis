import papis.arxiv

def test_general():
    data = papis.arxiv.get_data(
        author='Garnet Chan',
        max_results=1,
        title='Finite Temperature'
    )
    assert(data)
    assert(len(data) == 1)
