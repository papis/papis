from papis.importer import Importer


class PubMedImporter(Importer):
    """Importer downloading data from a PubMed ID."""

    def __init__(self, uri: str) -> None:
        super().__init__(name="pubmed", uri=uri)

    @classmethod
    def match(cls, uri: str) -> "PubMedImporter | None":
        from papis.pubmed import is_valid_pmid

        if is_valid_pmid(uri):
            return PubMedImporter(uri)

        return None

    def fetch_data(self) -> None:
        from papis.pubmed import get_data
        self.ctx.data = get_data(self.uri)
