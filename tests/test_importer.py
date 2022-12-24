from papis.importer import (
    Importer, Context, cache, get_importer_by_name, available_importers
)
import time


def test_context():
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


def test_cache():
    data = {"time": time.time()}

    class SimpleImporter(Importer):

        def __init__(self, uri="", **kwargs):
            super().__init__(uri=uri, name="SimpleImporter", **kwargs)

        @classmethod
        def match(cls, uri):
            importer = SimpleImporter(uri=uri)
            importer.ctx.data = data
            return importer

        @cache
        def fetch(self):
            time.sleep(.1)
            self.ctx.data = {"time": time.time()}

    importer = SimpleImporter()
    importer.fetch()
    assert importer.ctx
    assert not importer.ctx.data["time"] == data["time"]

    importer = SimpleImporter.match("uri")
    importer.fetch()
    assert importer.ctx.data["time"] == data["time"]


def test_get_importer():
    names = available_importers()
    assert isinstance(names, list)
    assert names
    for name in names:
        assert get_importer_by_name(name) is not None
