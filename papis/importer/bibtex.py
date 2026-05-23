from __future__ import annotations

from papis.importer import Importer


class BibTeXImporter(Importer):
    """
    Importer that parses BibTeX files or strings.

    Here, `uri` can either be a BibTeX string, local BibTeX file or a remote URL
    (with a HTTP or HTTPS protocol).
    """

    def __init__(self, uri: str) -> None:
        super().__init__(name="bibtex", uri=uri)

    @classmethod
    def match(cls, uri: str) -> BibTeXImporter | None:
        from papis.downloaders import download_document
        from papis.paths import is_remote_file

        # NOTE: we have no particular way of knowing if a remote file is a BibTeX
        # file, so we just download it and try to parse it.
        if is_remote_file(uri):
            filename = download_document(uri, expected_document_extension="bib")
            if filename is None:
                return None
        else:
            filename = uri

        from papis.bibtex import bibtex_to_dict

        # FIXME: we should give the result to the importer if it worked, so that
        # we don't parse it twice. Not a big speed win in most cases, but still..
        try:
            result = bibtex_to_dict(filename)
        except Exception:
            return None

        return BibTeXImporter(filename) if result else None

    def fetch_data(self) -> None:
        self.logger.info("Reading input file or string: '%s'.", self.uri)

        from papis.downloaders import download_document
        from papis.paths import is_remote_file

        if is_remote_file(self.uri):
            filename = download_document(self.uri, expected_document_extension="bib")
        else:
            filename = self.uri

        from papis.bibtex import bibtex_to_dict

        try:
            bib_data = bibtex_to_dict(filename) if filename is not None else []
        except Exception as exc:
            self.logger.error("Error reading BibTeX file or string: '%s'.",
                              self.uri, exc_info=exc)
            return

        if not bib_data:
            self.logger.warning(
                "Failed parsing the following file or string: '%s'.", self.uri)
            return

        if len(bib_data) > 1:
            self.logger.warning(
                "The BibTeX file contains %d entries. Picking the first one!",
                len(bib_data))

        # TODO: check if the data has any "file" entries and load those too?
        self.ctx.data = bib_data[0]
