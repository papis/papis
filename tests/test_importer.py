from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import pytest

from papis.importer import Importer

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


def _make_fake_importer(name: str) -> type[Importer]:
    """Build a fake :class:`Importer` subclass (as a third-party plugin would)."""
    return type(name, (Importer,), {
        "name": name,
        "__module__": "tests.test_importer",
    })


def test_get_importer(tmp_config: TemporaryConfiguration,
                      monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.plugin
    from papis.importer import Importer, get_available_importers, get_importer_by_name
    from papis.plugin import PluginNotFoundError

    fake = _make_fake_importer("fake")
    monkeypatch.setattr(papis.plugin, "get_plugin_names",
                        lambda ns: ["fake"])

    def _get_plugin_by_name(ns: str, name: str) -> Any:
        if name == "fake":
            return fake
        raise PluginNotFoundError(ns, name)

    monkeypatch.setattr(papis.plugin, "get_plugin_by_name", _get_plugin_by_name)

    names = get_available_importers()
    assert names == ["fake"]
    assert get_importer_by_name("fake") is fake
    assert issubclass(get_importer_by_name("fake"), Importer)

    with pytest.raises(PluginNotFoundError):
        _ = get_importer_by_name("this_is_not_a_known_importer_hopefully")
