import pytest
import requests

from papis.testing import ResourceCache, TemporaryConfiguration

DBLP_KEYS_VALID = [
    "books/sp/02/ST2002",
    "conf/iccg/EncarnacaoAFFGM93",
    "journals/aam/Davis23",
    "phd/dnb/Wein23",
    "series/sci/2023-1062",
]

DBLP_KEYS_INVALID = [
    "books/sp/02",
    "books/sp/02/ST2002-unknown",
    "series/sci",
]


def get(code: int, url: str) -> requests.Response:
    assert url.startswith("https://dblp.org/rec")

    r = requests.Response()
    r.status_code = code
    return r


@pytest.mark.xfail(reason="dblp times out sometimes")
def test_valid_dblp_key(tmp_config: TemporaryConfiguration,
                        monkeypatch: pytest.MonkeyPatch,
                        has_connection: bool = True) -> None:
    from papis.dblp import is_valid_dblp_key

    with monkeypatch.context() as m:
        if not has_connection:
            m.setattr(requests.Session, "get", lambda self, url: get(200, url))

        for key in DBLP_KEYS_VALID:
            assert is_valid_dblp_key(key)

    with monkeypatch.context() as m:
        if not has_connection:
            m.setattr(requests.Session, "get", lambda self, url: get(404, url))

        for key in DBLP_KEYS_INVALID:
            assert not is_valid_dblp_key(key)


@pytest.mark.xfail(reason="dblp times out sometimes")
def test_importer_match(tmp_config: TemporaryConfiguration,
                        monkeypatch: pytest.MonkeyPatch,
                        has_connection: bool = True) -> None:
    from papis.dblp import Importer, DBLP_URL_FORMAT

    with monkeypatch.context() as m:
        if not has_connection:
            m.setattr(requests.Session, "get", lambda self, url: get(200, url))

        for key in DBLP_KEYS_VALID:
            url = DBLP_URL_FORMAT.format(uri=key)
            importer = Importer.match(url)
            assert importer is not None

            importer = Importer.match(key)
            assert importer is not None

        for key in DBLP_KEYS_INVALID:
            importer = Importer.match(key)
            assert importer is None

        for url in [
                "https://dblp.net/rec/books/sp/02/ST2002.html",
                "https://dblp.org/rec/books/sp/02/ST2002.bib",
                ]:
            importer = Importer.match(url)
            assert importer is None


@pytest.mark.resource_setup(cachedir="resources/dblp")
def test_importer_fetch(tmp_config: TemporaryConfiguration,
                        monkeypatch: pytest.MonkeyPatch,
                        resource_cache: ResourceCache) -> None:
    from papis.dblp import Importer, DBLP_URL_FORMAT

    url = DBLP_URL_FORMAT.format(uri=DBLP_KEYS_VALID[-1])
    infile = "dblp_1.bin"
    outfile = "dblp_1_out.json"

    def get_bib(self: requests.Session, bib_url: str) -> requests.Response:
        assert bib_url.endswith(".bib")

        r = requests.Response()
        r.status_code = 200
        r._content = resource_cache.get_remote_resource(infile, bib_url)

        return r

    with monkeypatch.context() as m:
        m.setattr(requests.Session, "get", get_bib)

        importer = Importer.match(url)
        assert importer is not None

        importer.fetch()
        extracted_data = importer.ctx.data
        expected_data = resource_cache.get_local_resource(outfile, extracted_data)

        assert extracted_data == expected_data
