from papis.testing import TemporaryConfiguration


def test_csl_export(tmp_config: TemporaryConfiguration) -> None:
    from papis.csl import export_document
    from papis.document import from_data

    doc = from_data({
        "type": "article",
        "author": "Albert Einstein",
        "author_list": [{"given": "Albert", "family": "Einstein"}],
        "title": "The Theory of Everything",
        "journal": "Nature",
        "year": 2350,
        "ref": "MyDocument"})

    result = export_document(doc, style_name="harvard1", formatter_name="rst")
    assert result == "Einstein, A., 2350. The Theory of Everything. :emphasis:`Nature`."


def test_csl_style_download(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.csl import exporter
    from papis.document import from_data

    doc = from_data({
        "type": "article",
        "author": "Albert Einstein",
        "author_list": [{"given": "Albert", "family": "Einstein"}],
        "title": "The Theory of Everything",
        "journal": "Nature",
        "year": 2350,
        "ref": "MyDocument"})

    papis.config.set("csl-style", "acm-siggraph")
    result = exporter([doc])

    assert result == "Einstein, A. 2350. The Theory of Everything. Nature."
