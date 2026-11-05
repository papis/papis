"""Tests for the legacy importer/downloader adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

import papis.plugin
from papis.importer import Importer

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


class _FakeLegacyImporter(Importer):
    """A minimal but functional legacy importer plugin."""

    name = "fake-legacy"

    def __init__(self, uri: str = "", **kwargs: Any) -> None:
        super().__init__(uri=uri, name=self.name, **kwargs)

    @classmethod
    def match(cls, uri: str) -> _FakeLegacyImporter | None:
        return cls(uri=uri) if uri == "fake://match" else None

    @classmethod
    def match_data(cls, data: dict[str, Any]) -> _FakeLegacyImporter | None:
        return cls() if "fake" in data else None

    def fetch_data(self) -> None:
        self.ctx.data.update({
            "title": "Fake Title",
            "pdf_url": "https://example.org/fake.pdf",
        })

    def fetch_files(self) -> None:
        self.ctx.files.append("/tmp/fake.pdf")


class _FetchOnlyImporter(Importer):
    name = "fetch-only"

    @classmethod
    def match(cls, uri: str) -> _FetchOnlyImporter:
        return cls(uri=uri)

    def fetch(self) -> None:
        self.ctx.data["title"] = "Fetch Only"
        self.ctx.files.append("/tmp/only.pdf")


class _EmptyImporter(Importer):
    name = "empty"

    @classmethod
    def match(cls, uri: str) -> _EmptyImporter:
        return cls(uri=uri)


def test_wrap_legacy_plugins(monkeypatch: pytest.MonkeyPatch) -> None:
    """Legacy plugins come back wrapped and marked as legacy."""
    from papis.importer import IMPORTER_NAMESPACE_NAME, Importer
    from papis.sources import legacy

    class FakeImporter(Importer):
        name = "fake-legacy"

    monkeypatch.setattr(
        papis.plugin,
        "get_plugins",
        lambda namespace: (
            {"fake-legacy": FakeImporter}
            if namespace == IMPORTER_NAMESPACE_NAME
            else {}
        ),
    )

    handlers = legacy.wrap_legacy_plugins()

    (handler_cls,) = handlers.values()
    assert handler_cls.name == "fake-legacy"
    assert getattr(handler_cls, "is_legacy", False)


def test_wrap_legacy_plugins_ignores_non_importers(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Plugins that are not Importer subclasses are skipped with a warning."""
    from papis.sources import legacy

    class NotAnImporter:
        pass

    monkeypatch.setattr(
        papis.plugin, "get_plugins", lambda namespace: {"bogus": NotAnImporter}
    )

    with caplog.at_level("WARNING", logger="papis.sources.legacy"):
        assert legacy.wrap_legacy_plugins() == {}

    records = [r for r in caplog.records if r.name == "papis.sources.legacy"]
    assert any(r.levelname == "WARNING" and "bogus" in r.message for r in records)


def test_legacy_adapter_match() -> None:
    """The adapter tries ``match_for_lookup`` on the input and ``match_data``
    on fields."""
    from papis.sources import legacy
    from papis.sources.handler import LookupInput

    handler_cls = legacy.wrap_legacy_plugin("fake-legacy", _FakeLegacyImporter)
    assert handler_cls.name == "fake-legacy"
    assert handler_cls.priority == 5

    matched = handler_cls.match_for_lookup(LookupInput(input="fake://match"))
    assert matched is not None

    # no input match -> falls back to the metadata matcher
    assert (
        handler_cls.match_for_lookup(LookupInput(input="other", fields={"fake": "1"}))
        is not None
    )

    # neither matches
    assert handler_cls.match_for_lookup(LookupInput(input="other", fields={})) is None


def test_legacy_adapter_match_not_implemented() -> None:
    """Default ``Importer.match``/``match_data`` raising means no match."""
    from papis.sources import legacy
    from papis.sources.handler import LookupInput

    class FieldsOnlyImporter(Importer):
        name = "fields-only"

        @classmethod
        def match_data(cls, data: dict[str, Any]) -> FieldsOnlyImporter | None:
            return cls() if "fake" in data else None

    handler_cls = legacy.wrap_legacy_plugin("fields-only", FieldsOnlyImporter)
    matched = handler_cls.match_for_lookup(LookupInput(input="x", fields={"fake": "1"}))
    assert matched is not None
    assert handler_cls.match_for_lookup(LookupInput(input="x", fields={})) is None

    class UriOnlyImporter(Importer):
        name = "uri-only"

        @classmethod
        def match(cls, uri: str) -> UriOnlyImporter | None:
            return None

    handler_cls = legacy.wrap_legacy_plugin("uri-only", UriOnlyImporter)
    assert (
        handler_cls.match_for_lookup(LookupInput(input="x", fields={"fake": "1"}))
        is None
    )


@pytest.mark.parametrize(
    ("importer_cls", "title", "files"),
    [
        (_FakeLegacyImporter, "Fake Title", ["/tmp/fake.pdf"]),
        (_FetchOnlyImporter, "Fetch Only", ["/tmp/only.pdf"]),
        (_EmptyImporter, None, []),
    ],
)
def test_lookup_maps_the_context(
    tmp_config: TemporaryConfiguration,
    importer_cls: type[Importer],
    title: str | None,
    files: list[str],
) -> None:
    """The legacy context's data and files map onto the lookup output; the
    client discards what it does not want (legacy plugins download files
    themselves)."""
    import papis.config
    from papis.sources import legacy
    from papis.sources.handler import FileReference, LookupInput

    handler_cls = legacy.wrap_legacy_plugin(importer_cls.name, importer_cls)
    evidence = LookupInput(input="x", fields={"fake": "1"})
    matched = handler_cls.match_for_lookup(evidence)
    assert matched is not None

    result = matched.lookup(evidence)

    assert result.files == [FileReference(path=path) for path in files]
    assert result.followup is None
    if title is None:
        assert result.document is None
    else:
        assert result.document is not None
        assert result.document["title"] == title

    if importer_cls is _FakeLegacyImporter:
        # 'pdf_url' becomes the configured document URL key
        doc_url_key = papis.config.getstring("doc-url-key-name")
        assert result.document is not None
        assert result.document[doc_url_key] == "https://example.org/fake.pdf"


def test_wrap_legacy_plugins_downloaders(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Both plugin namespaces are wrapped; importers win name clashes."""
    from papis.downloaders import DOWNLOADERS_EXTENSION_NAME, Downloader
    from papis.importer import IMPORTER_NAMESPACE_NAME
    from papis.sources import legacy
    from papis.sources.handler import LookupInput

    class ImporterPlugin(Importer):
        name = "clash"

        @classmethod
        def match(cls, uri: str) -> ImporterPlugin:
            return cls(uri=uri)

    class DownloaderPlugin(Downloader):
        name = "clash"

        @classmethod
        def match(cls, uri: str) -> DownloaderPlugin:
            return cls(uri=uri)

    class DownloaderOnly(Downloader):
        name = "downloader-only"

        @classmethod
        def match(cls, uri: str) -> DownloaderOnly:
            return cls(uri=uri)

        def fetch_data(self) -> None:
            self.ctx.data["title"] = "Downloader Only"

    plugins = {
        IMPORTER_NAMESPACE_NAME: {"clash": ImporterPlugin},
        DOWNLOADERS_EXTENSION_NAME: {
            "clash": DownloaderPlugin,
            "downloader-only": DownloaderOnly,
        },
    }
    monkeypatch.setattr(papis.plugin, "get_plugins", plugins.__getitem__)

    handlers = legacy.wrap_legacy_plugins()
    assert set(handlers) == {"clash", "downloader-only"}

    # the clash is resolved in favour of the importer namespace, with a warning
    assert any(
        r.levelname == "WARNING" and "'clash'" in r.message
        for r in caplog.records
        if r.name == "papis.sources.legacy"
    )

    # the importer namespace is visited first, so it wins the name clash
    clash = handlers["clash"].match_for_lookup(LookupInput(input="x"))
    assert clash is not None
    assert isinstance(getattr(clash, "importer", None), ImporterPlugin)

    only = handlers["downloader-only"].match_for_lookup(LookupInput(input="x"))
    assert only is not None
    result = only.lookup(LookupInput(input="x"))
    assert result.document == {"title": "Downloader Only"}


def test_legacy_lookup_end_to_end(
    tmp_config: TemporaryConfiguration, handler_registry: Any
) -> None:
    """A wrapped legacy importer runs through the real lookup flow."""
    import papis.config
    from papis.sources import legacy
    from papis.sources.handler import FileReference, LookupInput
    from papis.sources.lookup import lookup

    handler_cls = legacy.wrap_legacy_plugin("fake-legacy", _FakeLegacyImporter)
    handler_registry(handler_cls)

    [result] = lookup(LookupInput(input="fake://match"))
    assert result.source == "fake-legacy"
    assert result.priority == 5
    assert result.status == "ok"
    assert result.document == {
        "title": "Fake Title",
        papis.config.getstring("doc-url-key-name"): "https://example.org/fake.pdf",
    }
    assert result.files == [FileReference(path="/tmp/fake.pdf")]
