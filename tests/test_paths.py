from papis.testing import TemporaryConfiguration


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


def test_normalize_path(tmp_config: TemporaryConfiguration) -> None:
    from papis.paths import normalize_path

    assert (
        normalize_path("{{] __ }}albert )(*& $ß $+_ einstein (*]")
        == "albert-ss-einstein"
    )
    assert (
        normalize_path('/ashfd/df/  #$%@#$ }{_+"[ ]hello öworld--- .pdf')
        == "hello-oworld-.pdf"
    )
    assert normalize_path("масса и енергиа.pdf") == "massa-i-energia.pdf"
    assert normalize_path("الامير الصغير.pdf") == "lmyr-lsgyr.pdf"


def test_normalize_path_config(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    from papis.paths import normalize_path

    papis.config.set("doc-paths-lowercase", "False")
    assert (
        normalize_path("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "Albert-ss-Einstein"
    )

    papis.config.set("doc-paths-extra-chars", "_")
    assert (
        normalize_path("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "__-Albert-ss-_-Einstein"
    )
    assert (
        normalize_path("{{] __Albert )(*& $ß $+_ Einstein (*]")
        == "__Albert-ss-_-Einstein"
    )

    papis.config.set("doc-paths-word-separator", "_")
    assert (
        normalize_path("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "___Albert_ss___Einstein"
    )

    papis.config.set("doc-paths-lowercase", "True")
    assert (
        normalize_path("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "___albert_ss___einstein"
    )
