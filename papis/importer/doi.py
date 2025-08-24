import os
from typing import Any

from papis.importer import Importer


class DOIImporter(Importer):
    """Importer getting files and data from a DOI (Digital Object Identifier)."""

    def __init__(self, uri: str, doi: str) -> None:
        super().__init__(name="doi", uri=uri)
        self.doi = doi

    @classmethod
    def match(cls, uri: str) -> "DOIImporter | None":
        from doi import validate_doi

        from papis.crossref import DOI_ORG_URL

        try:
            validate_doi(uri)
        except ValueError:
            return None
        else:
            return DOIImporter(f"{DOI_ORG_URL}/{uri}", uri)

    @classmethod
    def match_data(cls, data: dict[str, Any]) -> "DOIImporter | None":
        if "doi" in data:
            from papis.crossref import DOI_ORG_URL

            doi = data["doi"]
            return DOIImporter(f"{DOI_ORG_URL}/{doi}", doi)

        return None

    def fetch_data(self) -> None:
        from papis.crossref import get_data

        data = get_data(dois=[self.uri])
        if data:
            self.ctx.data = data[0]

    def fetch_files(self) -> None:
        if not self.ctx.data:
            return

        from papis.config import getstring

        doc_url_key_name = getstring("doc-url-key-name")
        doc_url = self.ctx.data.get(doc_url_key_name)

        if doc_url is None:
            return

        self.logger.info("Trying to download document from '%s'.", doc_url)

        from papis.downloaders import download_document

        filename = download_document(doc_url)
        if filename is not None:
            self.ctx.files.append(filename)


class DOIFromPDFImporter(DOIImporter):
    """Importer parsing a DOI from a PDF file."""

    def __init__(self, uri: str, doi: str) -> None:
        super().__init__(uri, doi)
        self.name = "pdf2doi"

    @classmethod
    def match(cls, uri: str) -> "DOIFromPDFImporter | None":
        from papis.filetype import get_document_extension

        if (not os.path.exists(uri)
                or os.path.isdir(uri)
                or get_document_extension(uri) != "pdf"):
            return None

        from doi import pdf_to_doi

        doi = pdf_to_doi(uri, maxlines=200)
        if not doi:
            return None

        imp = DOIFromPDFImporter(uri, doi)
        imp.logger.info("Parsed DOI '%s' from file: '%s'.", doi, uri)
        imp.logger.warning("There is no guarantee that this DOI is the correct one!")

        return imp

    @classmethod
    def match_data(cls, data: dict[str, Any]) -> "DOIFromPDFImporter | None":
        raise NotImplementedError

    def fetch_files(self) -> None:
        self.ctx.files.append(self.uri)
