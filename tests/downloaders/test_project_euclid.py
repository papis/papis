import os
import pytest

import papis.downloaders
from papis.downloaders.projecteuclid import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

PROJECT_EUCLID_URLS = (
    "https://projecteuclid.org/journals/advances-in-differential-equations/volume-19/"
    "issue-3_2f_4/An-analysis-of-the-renormalization-group-method-for-asymptotic"
    "-expansions/ade/1391109086.short",
    "https://projecteuclid.org/journals/duke-mathematical-journal/volume-164/"
    "issue-13/Delocalization-of-eigenvectors-of-random-matrices-with-independent"
    "-entries/10.1215/00127094-3129809.short"
    )


@pytest.mark.parametrize("url", PROJECT_EUCLID_URLS)
def test_project_euclid_fetch(tmp_config: TemporaryConfiguration,
                              resource_cache: ResourceCache,
                              monkeypatch: pytest.MonkeyPatch,
                              url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("projecteuclid")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url[:-6]).replace("-", "_")
    infile = f"ProjectEuclid_{uid}.html"
    outfile = f"ProjectEuclid_{uid}_Out.json"

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex add some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
