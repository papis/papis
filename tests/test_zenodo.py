import pytest

from papis.testing import ResourceCache, TemporaryLibrary


@pytest.mark.resource_setup(cachedir="resources/zenodo")
@pytest.mark.parametrize("markdownify", [True, False])
@pytest.mark.parametrize("zenodo_id", ["7391177", "10794563"])
def test_zenodo_id_to_data(tmp_library: TemporaryLibrary,
                           resource_cache: ResourceCache,
                           monkeypatch: pytest.MonkeyPatch,
                           markdownify: bool,
                           zenodo_id: str) -> None:
    import papis.zenodo

    if markdownify:
        from importlib.metadata import version

        pytest.importorskip("markdownify")
        v = "_" if version("markdownify") >= "0.14" else "_pre_0_14_"
    else:
        v = "_html_"
        monkeypatch.setattr(
            papis.zenodo, "_get_text_from_html",
            lambda html: html)

    infile = f"{zenodo_id}.json"
    outfile = f"{zenodo_id}{v}out.json"

    monkeypatch.setattr(
        papis.zenodo, "_get_zenodo_response",
        lambda zid: resource_cache.get_remote_resource(
            infile, papis.zenodo.ZENODO_URL.format(record_id=zid)
            ).decode()
    )

    input_data = papis.zenodo.get_data(zenodo_id)
    actual_data = papis.zenodo.zenodo_data_to_papis_data(input_data)
    expected_data = resource_cache.get_local_resource(outfile, actual_data)

    assert expected_data == actual_data
