import os

from papis.importer import Importer


class ArxivImporter(Importer):
    """Importer from arXiv URLs or identifiers."""

    def __init__(self, uri: str, arxivid: str) -> None:
        from papis.downloaders.arxiv import ArxivDownloader

        super().__init__(name="arxiv", uri=uri)

        # FIXME: this should not rely on the downloader to work => introduce some
        # helper functions or something that they can share
        self.downloader = ArxivDownloader(uri, arxivid)

    @property
    def arxivid(self) -> str:
        return self.downloader.arxivid

    @property
    def url(self) -> str:
        from papis.arxiv import ARXIV_ABS_URL
        return f"{ARXIV_ABS_URL}/{self.arxivid}"

    @classmethod
    def match(cls, uri: str) -> "ArxivImporter | None":
        from papis.arxiv import ARXIV_ABS_URL, find_arxivid_in_text, is_arxivid

        arxivid = find_arxivid_in_text(uri)
        if arxivid:
            return ArxivImporter(uri, arxivid)

        if is_arxivid(uri):
            return ArxivImporter(f"{ARXIV_ABS_URL}/{uri}", uri)

        return None

    def fetch_data(self) -> None:
        self.downloader.fetch_data()
        self.ctx.data = self.downloader.ctx.data.copy()

    def fetch_files(self) -> None:
        self.downloader.fetch_files()
        self.ctx.files = self.downloader.ctx.files.copy()


class ArxivFromPDFImporter(ArxivImporter):
    """Import from PDF files that contain arXiv identifiers."""

    def __init__(self, uri: str, arxivid: str) -> None:
        super().__init__(uri, arxivid)
        self.name = "pdf2arxivid"

    @classmethod
    def match(cls, uri: str) -> "ArxivFromPDFImporter | None":
        from papis.filetype import get_document_extension

        if not os.path.exists(uri) or os.path.isdir(uri):
            return None

        if get_document_extension(uri) != "pdf":
            return None

        from papis.arxiv import pdf_to_arxivid

        arxivid = pdf_to_arxivid(uri, maxlines=2000)
        return ArxivFromPDFImporter(uri, arxivid) if arxivid else None

    def fetch_files(self) -> None:
        self.ctx.files.append(self.uri)
