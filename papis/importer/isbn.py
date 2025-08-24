from papis.importer import Importer


class ISBNImporter(Importer):
    """Importer for ISBN identifiers through ``isbnlib``."""

    def __init__(self, uri: str) -> None:
        super().__init__(name="isbn", uri=uri)

    @classmethod
    def match(cls, uri: str) -> "ISBNImporter | None":
        from isbnlib import notisbn

        if notisbn(uri):
            return None

        return ISBNImporter(uri=uri)

    def fetch_data(self) -> None:
        from isbnlib import ISBNLibException

        from papis.isbn import data_to_papis, get_data

        try:
            data = get_data(self.uri)
        except ISBNLibException:
            data = None

        if data:
            self.ctx.data = data_to_papis(data[0])
