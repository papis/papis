def test_unique_suffixes() -> None:
    import string
    from papis.paths import unique_suffixes

    expected = [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
        "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
        "AA", "AB", "AC", "AD"
    ]
    for value, output in zip(expected, unique_suffixes(string.ascii_uppercase)):
        assert output == value

    for value, output in zip(expected[3:], unique_suffixes(skip=3)):
        assert output == value
