import re

from papis.importer import Importer


class DBLPImporter(Importer):
    """Importer for DBLP data from a key or URL."""

    def __init__(self, uri: str) -> None:
        super().__init__(name="dblp", uri=uri)

    @classmethod
    def match(cls, uri: str) -> "DBLPImporter | None":
        from papis.dblp import DBLP_URL_FORMAT, is_valid_dblp_key

        if re.match(r".*dblp\.org.*\.html", uri):
            return DBLPImporter(uri)
        elif is_valid_dblp_key(uri):
            return DBLPImporter(uri=DBLP_URL_FORMAT.format(uri=uri))
        else:
            return None

    def _get_body(self, url: str) -> str:
        from papis.utils import get_session

        with get_session() as session:
            response = session.get(url)

        if not response.ok:
            self.logger.error("Could not get BibTeX entry for '%s'.", self.uri)
            return

        return response.content.decode()

    def fetch_data(self) -> None:
        from papis.dblp import DBLP_BIB_FORMAT, is_valid_dblp_key

        # uri: https://dblp.org/rec/conf/iccg/EncarnacaoAFFGM93.html
        # bib: https://dblp.org/rec/conf/iccg/EncarnacaoAFFGM93.bib
        if is_valid_dblp_key(self.uri):
            url = DBLP_BIB_FORMAT.format(uri=self.uri)
        else:
            url = f"{self.uri[:-5]}.bib"

        from papis.bibtex import bibtex_to_dict

        entries = bibtex_to_dict(self._get_body(url))
        if not entries:
            return

        if len(entries) > 1:
            self.logger.warning("Found %d BibTeX entries for '%s'. Picking first one!",
                                len(entries), self.uri)

        self.ctx.data.update(entries[0])
