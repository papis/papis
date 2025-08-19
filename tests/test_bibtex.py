import os
import re

import pytest

from papis.testing import ResourceCache, TemporaryConfiguration

BIBTEX_RESOURCES = os.path.join(os.path.dirname(__file__), "resources", "bibtex")


def test_bibtex_to_dict(tmp_config: TemporaryConfiguration) -> None:
    from papis.bibtex import bibtex_to_dict

    bibpath = os.path.join(BIBTEX_RESOURCES, "1.bib")
    bib, = bibtex_to_dict(bibpath)
    expected_keys = {
        "title",
        "author",
        "journal",
        "abstract",
        "volume",
        "issue",
        "pages",
        "numpages",
        "year",
        "month",
        "publisher",
        "doi",
        "url",
        }

    assert not (expected_keys - bib.keys())
    assert bib["type"] == "article"
    assert re.match(r".*Rev.*", bib["journal"])
    assert re.match(r".*concurrent inter.*", bib["abstract"])


def test_bibkeys_exist(tmp_config: TemporaryConfiguration) -> None:
    from papis.bibtex import bibtex_keys
    assert len(bibtex_keys) != 0


def test_bibtypes_exist(tmp_config: TemporaryConfiguration) -> None:
    from papis.bibtex import bibtex_types
    assert len(bibtex_types) != 0


@pytest.mark.parametrize("bibfile", ["1.bib", "2.bib", "3.bib"])
def test_author_list_conversion(
        tmp_config: TemporaryConfiguration,
        resource_cache: ResourceCache,
        bibfile: str,
        overwrite: bool = False) -> None:
    basename, _ = os.path.splitext(bibfile)
    jsonfile = f"bibtex/{basename}_out.json"

    from papis.bibtex import bibtex_to_dict

    bib, = bibtex_to_dict(os.path.join(BIBTEX_RESOURCES, bibfile))
    expected = resource_cache.get_local_resource(jsonfile, bib)

    assert bib["author_list"] == expected["author_list"]


def test_clean_ref(tmp_config: TemporaryConfiguration) -> None:
    from papis.bibtex import ref_cleanup

    for (r, rc) in [
            ("Einstein über etwas und so 1923", "Einstein_uber_etwas_und_so_1923"),
            ("Äöasf () : Aλבert Eιنς€in", "Aoasf_Albert_EinsEURin"),  # noqa: RUF001
            (r"Albert_Ein\_stein\.1923.b", "Albert_Ein__stein_.1923_b"),
            ]:
        assert rc == ref_cleanup(r)


def test_to_bibtex_wrong_type(tmp_config: TemporaryConfiguration) -> None:
    """Test no BibTeX entry is constructed for incorrect types."""
    from papis.document import from_data

    doc = from_data({
        "type": "fictional",
        "ref": "MyDocument",
        "author": "Albert Einstein",
        "title": "The Theory of Everything",
        "journal": "Nature",
        "year": 2350
        })

    from papis.exporters.bibtex import exporter

    result = exporter([doc])
    assert not result


def test_to_bibtex_no_ref(tmp_config: TemporaryConfiguration) -> None:
    """Test no BibTeX entry is constructed for invalid references."""
    from papis.document import from_data
    doc = from_data({
        "type": "techreport",
        "author": "Albert Einstein",
        "title": "The Theory of Everything",
        "journal": "Nature",
        "year": 2350,
        })

    # NOTE: this seems to be one of the few ways to fail the ref construction,
    # i.e. set it to some invalid characters.
    from papis.config import set as setstring
    setstring("ref-format", "--")

    from papis.exporters.bibtex import exporter
    result = exporter([doc])
    assert not result


def test_to_bibtex_formatting(tmp_config: TemporaryConfiguration) -> None:
    """Test formatting for the BibTeX exporter."""
    from papis.document import from_data
    from papis.exporters.bibtex import exporter

    assert exporter([from_data({
        "type": "report",
        "author": "Albert Einstein",
        "author_list": [{"given": "Albert", "family": "Einstein"}],
        "title": "The Theory of Everything",
        "journal": "Nature",
        "year": 2350,
        "ref": "MyDocument"})
        ]) == (
        "@report{MyDocument,\n"
        "  author = {Einstein, Albert},\n"
        "  journal = {Nature},\n"
        "  title = {The Theory of Everything},\n"
        "  year = {2350},\n"
        "}")

    assert exporter([from_data({
        "type": "misc",
        "ref": "SDbwLashko2019",
        "author": "Alexander Lashkov",
        "author_list": [{"given": "Alexander", "family": "Lashkov"}],
        "url": "https://github.com/alashkov83/S_Dbw"})
        ]) == (
        "@misc{SDbwLashko2019,\n"
        "  author = {Lashkov, Alexander},\n"
        "  url = {https://github.com/alashkov83/S_Dbw},\n"
        "}")


def test_overridable(tmp_config: TemporaryConfiguration) -> None:
    from papis.config import set as setboolean
    from papis.document import from_data
    from papis.exporters.bibtex import exporter

    doc = {
        "type": "report",
        "author": "Albert Einstein",
        "author_list": [{"given": "Albert", "family": "Einstein"}],
        "title": "Ä α The Theory of Everything & Nothing",  # noqa: RUF001
        "title_latex": r"The Theory of Everything \& Nothing",
        "journal": "Nature",
        "year": 2350,
        "ref": "MyDocument"
    }

    setboolean("bibtex-unicode", True)
    assert exporter([from_data(doc)]) == (
        "@report{MyDocument,\n"
        "  author = {Einstein, Albert},\n"
        "  journal = {Nature},\n"
        "  title = {The Theory of Everything \\& Nothing},\n"
        "  year = {2350},\n"
        "}")

    setboolean("bibtex-unicode", False)
    assert exporter([from_data(doc)]) == (
        "@report{MyDocument,\n"
        "  author = {Einstein, Albert},\n"
        "  journal = {Nature},\n"
        "  title = {The Theory of Everything "
        # this will sadly happen, and it makes sense
        r"\textbackslash \&"
        " Nothing},\n"
        "  year = {2350},\n"
        "}")


def test_ignore_keys(tmp_config: TemporaryConfiguration,
                     monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.bibtex
    from papis.config import getlist, set as setlist
    from papis.document import from_data
    from papis.exporters.bibtex import exporter

    doc = {
        "type": "report",
        "author": "Albert Einstein",
        "author_list": [{"given": "Albert", "family": "Einstein"}],
        "year": 2350,
        "ref": "MyDocument"
    }
    assert exporter([from_data(doc)]) == (
        "@report{MyDocument,\n"
        "  author = {Einstein, Albert},\n"
        "  year = {2350},\n"
        "}")

    # TODO: think about this since these keys are not updated
    #       dynamically and it's possible is not worth it to update dynamically
    setlist("bibtex-ignore-keys", ["year"])
    monkeypatch.setattr(papis.bibtex, "bibtex_ignore_keys",
                        frozenset(getlist("bibtex-ignore-keys")))

    assert exporter([from_data(doc)]) == (
        "@report{MyDocument,\n"
        "  author = {Einstein, Albert},\n"
        "}")


def test_import_institution(tmp_config: TemporaryConfiguration) -> None:
    from papis.bibtex import bibtex_to_dict
    from papis.exporters.bibtex import exporter

    orig = (
        "@report{ipcc1990,\n"
        "  author = {{Intergovernmental Panel on Climate Change}},\n"
        "  title = {Contribution of Working Group I to the First Assessment "
        "Report of the Intergovernmental Panel on Climate Change},\n"
        "  year = {1990},\n"
        "}"
    )
    to_result, = bibtex_to_dict(orig)

    author, = to_result["author_list"]
    assert not author["given"]
    assert author["family"] == "Intergovernmental Panel on Climate Change"

    from papis.document import from_data

    from_result = exporter([from_data(to_result)])
    assert from_result == orig
