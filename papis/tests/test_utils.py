import papis.utils


def test_create_identifier():
    import itertools
    import string
    output = list(
        itertools.islice(
            papis.utils.create_identifier(string.ascii_uppercase),
            30
        )
    )
    expected = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        'AA', 'AB', 'AC', 'AD'
    ]
    for i in range(30):
        assert(output[i] == expected[i])
