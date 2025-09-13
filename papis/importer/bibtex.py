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
    def match(cls, uri: str) -> "BibTeXImporter | None":
        # FIXME: this should not do a full download + parse just to check if this
        # might be a BibTeX file
        importer = BibTeXImporter(uri=uri)
        importer.fetch()

        return importer if importer.ctx else None

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
