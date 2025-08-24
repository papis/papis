import time
from typing import Any

import pytest

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
        def match(cls, uri: str) -> "CustomContextImporter":
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
        def match(cls, uri: str) -> "SimpleImporter":
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


def test_get_matching_importers_by_name(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer import get_matching_importers_by_name
    from papis.importer.doi import DOIImporter

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

    from papis.downloaders.usenix import Downloader as UsenixDownloader

    importers = get_matching_importers_by_name(name_and_uris, include_downloaders=True)
    assert len(importers) == 2
    assert isinstance(importers[0], DOIImporter)
    assert isinstance(importers[1], UsenixDownloader)


def test_matching_importers_by_uri(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer import get_matching_importers_by_uri

    importers = get_matching_importers_by_uri("this_is_not_an_uri")
    assert len(importers) == 0

    from papis.importer.arxiv import ArxivImporter

    importers = get_matching_importers_by_uri("https://arxiv.org/abs/1110.3658")
    assert len(importers) == 1
    assert isinstance(importers[0], ArxivImporter)

    from papis.downloaders.fallback import Downloader as FallbackDownloader
    from papis.downloaders.usenix import Downloader as UsenixDownloader

    importers = get_matching_importers_by_uri(
        "https://www.usenix.org/conference/nsdi22/presentation/goyal",
        include_downloaders=True)
    assert len(importers) == 2
    assert isinstance(importers[0], FallbackDownloader)
    assert isinstance(importers[1], UsenixDownloader)


def test_matching_importers_by_doc(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer import get_matching_importers_by_doc
    from papis.importer.doi import DOIImporter

    doc = {"doi": "10.1103/physrevb.89.140501"}
    importers = get_matching_importers_by_doc(doc)
    assert len(importers) == 1
    assert isinstance(importers[0], DOIImporter)
