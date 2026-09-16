from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def test_csl_export(tmp_config: TemporaryConfiguration) -> None:
    citeproc = pytest.importorskip("citeproc")

    from papis.document import from_data
    from papis.exporters.csl import export_documents

    doc = from_data({
        "type": "article",
        "author": "Albert Einstein",
        "author_list": [{"given": "Albert", "family": "Einstein"}],
        "title": "The Theory of Everything",
        "journal": "Nature",
        "year": 2350,
        "pages": "1-24",
        "ref": "MyDocument"})

    results = export_documents([doc], style_name="harvard1", formatter_name="rst")
    result = results[0]

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


NUMBERED_CSL_STYLE = """\
<?xml version="1.0" encoding="utf-8"?>
<style xmlns="http://purl.org/net/xbiblio/csl" class="in-text" version="1.0">
  <info>
    <title>Numbered Test</title>
    <id>http://example.com/numbered-test</id>
    <updated>2020-01-01T00:00:00+00:00</updated>
  </info>
  <citation>
    <layout>
      <text variable="citation-number" prefix="[" suffix="]"/>
    </layout>
  </citation>
  <bibliography>
    <layout>
      <text variable="citation-number" prefix="[" suffix="] "/>
      <text variable="title"/>
    </layout>
  </bibliography>
</style>
"""


def test_csl_export_multiple_documents(
        tmp_config: TemporaryConfiguration) -> None:
    pytest.importorskip("citeproc")

    import os

    import papis.config
    from papis.document import from_data
    from papis.exporters.csl import exporter

    style_path = os.path.join(tmp_config.tmpdir, "numbered.csl")
    with open(style_path, "w", encoding="utf-8") as fout:
        fout.write(NUMBERED_CSL_STYLE)

    docs = [
        from_data({
            "type": "article",
            "author_list": [{"given": "Albert", "family": "Einstein"}],
            "title": "Doc One",
            "year": 2350,
            "ref": "DocOne"}),
        from_data({
            "type": "article",
            "author_list": [{"given": "Isaac", "family": "Newton"}],
            "title": "Doc Two",
            "year": 2360,
            "ref": "DocTwo"}),
    ]

    papis.config.set("csl-style", style_path)
    papis.config.set("csl-formatter", "plain")
    result = exporter(docs)

    assert result == "[1] Doc One\n\n[2] Doc Two"
