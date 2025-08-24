from typing import Any

from papis.importer import Importer


class CrossrefImporter(Importer):
    """Importer that gets data from querying Crossref."""

    def __init__(self, uri: str) -> None:
        super().__init__(name="crossref", uri=uri)

    @classmethod
    def match(cls, uri: str) -> "CrossrefImporter | None":
        # There is no way to check if it matches
        return None

    @classmethod
    def match_data(cls, data: dict[str, Any]) -> "CrossrefImporter | None":
        if "title" in data:
            return CrossrefImporter(uri=data["title"])

        return None

    def fetch_data(self) -> None:
        from papis.crossref import get_data

        self.logger.info("Querying Crossref with '%s'.", self.uri)
        results = get_data(query=self.uri)

        if not results:
            return

        self.logger.warning(
            "Crossref query '%s' returned %d results. Picking the first one!",
            self.uri, len(results))

        self.ctx.data = results[0]
