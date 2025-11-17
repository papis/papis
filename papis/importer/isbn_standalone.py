from __future__ import annotations

from papis.importer import Importer


class ISBNStandaloneImporter(Importer):
    """Importer for ISBN identifiers."""

    def __init__(self, uri: str) -> None:
        super().__init__(name="isbn", uri=uri)

    @classmethod
    def match(cls, uri: str) -> ISBNStandaloneImporter | None:
        from papis.isbn_standalone import notisbn

        if notisbn(uri):
            return None

        return ISBNStandaloneImporter(uri=uri)

    def fetch_data(self) -> None:
        from papis.isbn import data_to_papis, get_data

        data = get_data(self.uri)

        if data:
            self.ctx.data = data_to_papis(data[0])
