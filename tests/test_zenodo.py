import pytest

from papis.testing import TemporaryLibrary, ResourceCache


@pytest.mark.resource_setup(cachedir="resources/zenodo")
@pytest.mark.parametrize("zenodo_id", ["7391177", "10794563"])
def test_zenodo_id_to_data(tmp_library: TemporaryLibrary,
                           resource_cache: ResourceCache,
                           monkeypatch: pytest.MonkeyPatch,
                           zenodo_id: str) -> None:
    # NOTE: the functionality doesn't require markdownify, but the output files
    # are formatted using it so the test would fail otherwise.
    pytest.importorskip("markdownify")

    import papis.zenodo

    infile = "{}.json".format(zenodo_id)
    outfile = "{}_out.json".format(zenodo_id)

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
