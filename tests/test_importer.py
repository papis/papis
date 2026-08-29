from __future__ import annotations

import os
import re
import time
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def test_context(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer import Context

    ctx = Context()
    assert ctx.data == {}
    assert ctx.files == []
    assert not ctx

    ctx.files = ["a"]
    assert ctx

    ctx.files = []
    ctx.data["key"] = 42
    assert ctx


def test_custom_context_importer(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer import Context, Importer

    class CustomContext(Context):
        def __init__(self) -> None:
            super().__init__()
            self.extra = ""

    class CustomContextImporter(Importer):
        ctx: CustomContext

        def __init__(self, uri: str = "", **kwargs: Any) -> None:
            super().__init__(uri=uri, name="SimpleImporter", ctx=CustomContext())

        @classmethod
        def match(cls, uri: str) -> CustomContextImporter:
            importer = CustomContextImporter(uri=uri, ctx=CustomContext())
            return importer

        def fetch(self) -> None:
            self.ctx.extra = "foobar"

    importer = CustomContextImporter()
    assert importer.ctx.extra == ""
    importer.fetch()
    assert importer.ctx.extra == "foobar"


def test_cache(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer import Importer, cache

    data = {"time": time.time()}

    class SimpleImporter(Importer):

        def __init__(self, uri: str = "", **kwargs: Any) -> None:
            super().__init__(uri=uri, name="SimpleImporter", **kwargs)

        @classmethod
        def match(cls, uri: str) -> SimpleImporter:
            importer = SimpleImporter(uri=uri)
            importer.ctx.data = data
            return importer

        @cache
        def fetch(self) -> None:
            time.sleep(0.1)
            self.ctx.data = {"time": time.time()}

    importer = SimpleImporter()
    importer.fetch()
    assert importer.ctx
    assert not importer.ctx.data["time"] == data["time"]

    importer = SimpleImporter.match("uri")
    importer.fetch()
    assert importer.ctx.data["time"] == data["time"]


def test_get_importer(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer import Importer, get_available_importers, get_importer_by_name
    from papis.plugin import PluginNotFoundError

    names = get_available_importers()
    assert isinstance(names, list)
    assert names

    for name in names:
        cls = get_importer_by_name(name)
        assert issubclass(cls, Importer)

    with pytest.raises(PluginNotFoundError):
        _ = get_importer_by_name("this_is_not_a_known_importer_hopefully")


def _fake_validate_doi(doi: str) -> None:
    """Mimic :func:`doi.validate_doi` without querying doi.org."""
    if not re.match(r"10\.\d{4,9}/\S+", doi):
        raise ValueError(f"not a doi: {doi}")


def _patch_network_matching(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do importer matching without network.

    Some importers query remote services from within :meth:`Importer.match`. Patch those
    validators so that the tests here don't touch the network. The matching itself is
    tested in the relevant importer tests.
    """
    monkeypatch.setattr("doi.validate_doi", _fake_validate_doi)
    monkeypatch.setattr("papis.arxiv.is_arxivid", lambda arg: "arxiv" in arg)
    monkeypatch.setattr("papis.downloaders.download_document",
                        lambda *args, **kwargs: None)


def test_matching_importers_by_name(tmp_config: TemporaryConfiguration,
                                        monkeypatch: pytest.MonkeyPatch,
                                        ) -> None:
    from papis.importer import get_matching_importers_by_name
    from papis.importer.doi import DOIImporter

    _patch_network_matching(monkeypatch)

    name_and_uris = [
        # 1. a valid importer name + valid uri
        ("doi", "10.1103/physrevb.89.140501"),
        # 2. a valid importer name + invalid uri
        ("doi", "this_does_not_look_like_a_doi_hopefully"),
        # 3. an invalid importer name
        ("this_importer_does_not_exist", "unknown"),
        # 4. a downloader name + valid uri
        ("usenix",
         "https://www.usenix.org/conference/usenixsecurity22/presentation/bulekov"),
    ]

    importers = get_matching_importers_by_name(name_and_uris)
    assert len(importers) == 1
    assert isinstance(importers[0], DOIImporter)

    from papis.downloaders.usenix import USENIXDownloader

    importers = get_matching_importers_by_name(name_and_uris, include_downloaders=True)
    assert len(importers) == 2
    assert isinstance(importers[0], DOIImporter)
    assert isinstance(importers[1], USENIXDownloader)


def test_matching_importers_by_uri(tmp_config: TemporaryConfiguration,
                                   monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.importer import get_matching_importers_by_uri

    _patch_network_matching(monkeypatch)

    importers = get_matching_importers_by_uri("this_is_not_an_uri")
    assert len(importers) == 0

    from papis.importer.arxiv import ArxivImporter

    importers = get_matching_importers_by_uri("https://arxiv.org/abs/1110.3658")
    assert len(importers) == 1
    assert isinstance(importers[0], ArxivImporter)

    from papis.downloaders.fallback import FallbackDownloader
    from papis.downloaders.usenix import USENIXDownloader
    from papis.importer.bibtex import BibTeXImporter

    # NOTE: the URL has some embedded BibTeX that we do not care to catch here
    monkeypatch.setattr(BibTeXImporter, "match",
                        lambda *args, **kwargs: None)

    importers = get_matching_importers_by_uri(
        "https://www.usenix.org/conference/nsdi22/presentation/goyal",
        include_downloaders=True)
    assert len(importers) == 2
    assert isinstance(importers[0], FallbackDownloader)
    assert isinstance(importers[1], USENIXDownloader)


def test_doi_importer_does_not_match_local_paths(
        tmp_config: TemporaryConfiguration) -> None:
    import os

    from papis.importer.doi import DOIImporter

    # NOTE: a space makes the doi.org handle URL invalid, which used to crash
    # the importer matching instead of skipping it (see #1201)
    path = os.path.join(tmp_config.tmpdir, "some presentation.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("this is not a doi\n")

    assert DOIImporter.match(path) is None


def test_matching_importers_by_doc(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer import get_matching_importers_by_doc
    from papis.importer.doi import DOIImporter

    doc = {"doi": "10.1103/physrevb.89.140501"}
    importers = get_matching_importers_by_doc(doc)
    assert len(importers) == 1
    assert isinstance(importers[0], DOIImporter)


def test_fetch_importers_source_error(
        tmp_config: TemporaryConfiguration,
        caplog: pytest.LogCaptureFixture) -> None:
    from papis.exceptions import SourceError
    from papis.importer import Context, Importer, fetch_importers

    class FailingImporter(Importer):
        def __init__(self, uri: str = "", **kwargs: Any) -> None:
            super().__init__(uri="source-error", name="FailingImporter",
                             ctx=Context())

        @staticmethod
        def fetch() -> None:
            raise SourceError("boom")

    with caplog.at_level("ERROR"):
        assert fetch_importers([FailingImporter()]) == []

    assert "FailingImporter" in caplog.text


def _make_simple_importer(name: str, data: dict[str, Any],
                          files: list[str]) -> Any:
    from papis.importer import Importer

    importer = Importer(uri=name, name=name)
    importer.ctx.data = dict(data)
    importer.ctx.files = list(files)
    return importer


def test_collect_from_importers_batch(tmp_config: TemporaryConfiguration) -> None:
    """Checks that batch collection merges later importer data over earlier."""
    from papis.importer import collect_from_importers

    imp1 = _make_simple_importer("a",
                                 {"title": "t1", "year": 2000, "ref": "key-a"},
                                 ["f1.pdf"])
    imp2 = _make_simple_importer("b",
                                 {"title": "t2", "author": "A", "ref": "key-b"},
                                 ["f1.pdf", "f2.pdf"])

    ctx = collect_from_importers([imp1, imp2], batch=True)

    # later importers overwrite earlier data for the same key and the 'ref' key is
    # always dropped
    assert ctx.data == {"title": "t2", "year": 2000, "author": "A"}

    # files are concatenated and duplicates are kept
    assert ctx.files == ["f1.pdf", "f1.pdf", "f2.pdf"]


def test_collect_from_importers_interactive(
        tmp_config: TemporaryConfiguration,
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Checks that interactive collection only prompts for later importers."""
    import papis.utils
    from papis.importer import collect_from_importers

    calls: list[tuple[dict[str, Any], dict[str, Any], str]] = []

    def _update_interactively(doc: dict[str, Any], data: dict[str, Any],
                              name: str) -> None:
        calls.append((dict(doc), dict(data), name))

        # emulate a user that keeps existing values
        for key, value in data.items():
            if key not in doc:
                doc[key] = value

    monkeypatch.setattr(papis.utils, "update_doc_from_data_interactively",
                        _update_interactively)

    imp1 = _make_simple_importer("a", {"title": "t1", "year": 2000}, ["f1.pdf"])
    imp2 = _make_simple_importer("b", {"title": "t2", "author": "A"}, [])

    ctx = collect_from_importers([imp1, imp2], batch=False)

    assert len(calls) == 1
    assert calls[0][0] == {"title": "t1", "year": 2000}
    assert calls[0][1] == {"title": "t2", "author": "A"}

    assert ctx.data == {"title": "t1", "year": 2000, "author": "A"}
    assert ctx.files == ["f1.pdf"]


def test_bibtex_importer_multi_entry(tmp_config: TemporaryConfiguration,
                                     caplog: pytest.LogCaptureFixture) -> None:
    """Checks that multi-entry bibtex only keeps the first entry, with a warning."""
    from papis.importer.bibtex import BibTeXImporter

    bibtex_string = (
        "@article{first,\n"
        "  author = {A. One},\n"
        "  title = {First entry}\n"
        "}\n"
        "@article{second,\n"
        "  author = {B. Two},\n"
        "  title = {Second entry}\n"
        "}\n"
    )

    path = os.path.join(tmp_config.tmpdir, "multi.bib")
    with open(path, "w", encoding="utf-8") as f:
        f.write(bibtex_string)

    importer = BibTeXImporter.match(path)
    assert importer is not None
    importer.fetch_data()

    assert importer.ctx.data["title"] == "First entry"
    assert importer.ctx.data["author"] == "One, A."
    assert "2 entries" in caplog.text
    assert "Picking the first one" in caplog.text
