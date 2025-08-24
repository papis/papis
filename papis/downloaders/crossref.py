from papis.downloaders import Downloader


class CrossrefDownloader(Downloader):
    """Retrieve documents by DOI from `Crossref <https://www.crossref.org>`__"""

    def __init__(self, uri: str, doi: str) -> None:
        super().__init__(uri=uri, name="doi")
        self.doi = doi

    @classmethod
    def match(cls, uri: str) -> "CrossrefDownloader | None":
        from doi import find_doi_in_text

        doi = find_doi_in_text(uri)
        if not doi:
            return None

        return CrossrefDownloader(uri, doi)

    def fetch(self) -> None:
        if not self.doi:
            return

        from papis.importer.doi import DOIImporter

        importer = DOIImporter(self.uri, self.doi)
        importer.fetch()
        self.ctx = importer.ctx
