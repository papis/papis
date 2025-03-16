import time
from typing import Any

import pytest


def test_context() -> None:
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

    ctx = Context()
    assert not ctx


def test_custom_context_importer() -> None:
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


def test_cache() -> None:
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


def test_get_importer() -> None:
    from papis.importer import Importer, available_importers, get_importer_by_name
    from papis.plugin import PluginNotFoundError

    names = available_importers()
    assert isinstance(names, list)
    assert names

    for name in names:
        cls = get_importer_by_name(name)
        assert issubclass(cls, Importer)

    with pytest.raises(PluginNotFoundError):
        _ = get_importer_by_name("this_is_not_a_known_importer_hopefully")
