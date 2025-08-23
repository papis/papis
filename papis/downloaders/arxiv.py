from functools import cached_property
from typing import TYPE_CHECKING, Any

from papis.downloaders import Downloader

if TYPE_CHECKING:
    import arxiv


class ArxivDownloader(Downloader):
    """Retrieve documents from `arXiv <https://arxiv.org>`__"""

    def __init__(self, url: str, arxivid: str) -> None:
        super().__init__(uri=url, name="arxiv", expected_document_extension="pdf")
        self.arxivid = arxivid

    @classmethod
    def match(cls, url: str) -> "ArxivDownloader | None":
        from papis.arxiv import ARXIV_ABS_URL, find_arxivid_in_text

        arxivid = find_arxivid_in_text(url)
        if arxivid:
            return ArxivDownloader(f"{ARXIV_ABS_URL}/{arxivid}", arxivid)
        else:
            return None

    @cached_property
    def result(self) -> "arxiv.Result | None":
        import arxiv

        client = arxiv.Client()
        try:
            results = list(client.results(arxiv.Search(id_list=[self.arxivid])))
        except arxiv.ArxivError as exc:
            self.logger.error(
                "Failed to download metadata from arXiv: '%s'.",
                self.uri, exc_info=exc)
            results = []

        if not results:
            return None

        if len(results) > 1:
            self.logger.error(
                "Found multiple results for arxivid '%s'. Picking the first one!",
                self.arxivid)

        return results[0]

    def get_data(self) -> dict[str, Any]:
        result = self.result
        if result is None:
            return {}

        from papis.arxiv import arxiv_to_papis
        return arxiv_to_papis(self.result)

    def get_document_url(self) -> str | None:
        result = self.result
        if result is None:
            return None

        self.logger.debug("pdf_url = '%s'", result.pdf_url)
        return str(result.pdf_url)
