from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def test_csl_export(tmp_config: TemporaryConfiguration) -> None:
    citeproc = pytest.importorskip("citeproc")

    from papis.document import from_data
    from papis.exporters.csl import export_document

    doc = from_data({
        "type": "article",
        "author": "Albert Einstein",
        "author_list": [{"given": "Albert", "family": "Einstein"}],
        "title": "The Theory of Everything",
        "journal": "Nature",
        "year": 2350,
        "pages": "1-24",
        "ref": "MyDocument"})

    result = export_document(doc, style_name="harvard1", formatter_name="rst")

    # NOTE: older versions used a "harvard" style and newer versions use a
    # "harvard-cite-them-right" style that's quite different, see:
    #   https://github.com/citeproc-py/citeproc-py/pull/197
    version = tuple(int(v) for v in citeproc.__version__.split("+")[0].split("."))
    if version < (0, 10, 3):
        assert result == (
            # ruff: ignore[ambiguous-unicode-character-string]
            "Einstein, A., 2350. The Theory of Everything. :emphasis:`Nature`, pp.1–24."
        )
    else:
        assert result == (
            # ruff: ignore[ambiguous-unicode-character-string,line-too-long]
            "Einstein, A. (2350) “The Theory of Everything”, :emphasis:`Nature`, pp. 1–24."
        )


def test_csl_style_download(tmp_config: TemporaryConfiguration) -> None:
    pytest.importorskip("citeproc")

    import papis.config
    from papis.document import from_data
    from papis.exporters.csl import exporter

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
