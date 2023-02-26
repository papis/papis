import re
from typing import Any, ClassVar, Dict, Optional, Tuple

import papis.downloaders.fallback


class Downloader(papis.downloaders.fallback.Downloader):
    # NOTE: this only advertises subdomains maintained by CCSD
    # https://www.ccsd.cnrs.fr/2022/06/hal-archives-ouvertes-fr-va-devenir-hal-science/

    # TODO: a list of other domains seems to be available at
    # https://hal.science/browse/portal

    SUPPORTED_HAL_SCIENCE_SUBDOMAINS = (
        "hal", r"shs\.hal", r"theses\.hal", r"media\.hal",
        )   # type: ClassVar[Tuple[str, ...]]

    SUPPORTED_ARCHIVES_OUVERTES_SUBDOMAINS = (
        "hal", "halshs", "tel", "medihal",
        # other domains
        "hal-anr", "hal-bnf", "hal-cea", "hal-centralesupelec", "hal-cnam",
        "hal-cnrs",
        )   # type: ClassVar[Tuple[str, ...]]

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="hal",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(
            cls, url: str) -> Optional[papis.downloaders.fallback.Downloader]:
        subdomains = "|".join(cls.SUPPORTED_ARCHIVES_OUVERTES_SUBDOMAINS)
        if re.match(r".*({})\.archives-ouvertes\.fr.*".format(subdomains), url):
            return Downloader(url)

        subdomains = r"|".join(cls.SUPPORTED_HAL_SCIENCE_SUBDOMAINS)
        if re.match(r".*//({})\.science.*".format(subdomains), url):
            return Downloader(url)

        return None

    def get_data(self) -> Dict[str, Any]:
        data = super().get_data()

        keywords = data.get("keywords")
        if keywords is not None:
            # FIXME: also add to `tags`?
            data["keywords"] = [kw.strip() for kw in keywords.split(";")]

        bib_type = data.get("type")
        if bib_type is not None and "thesis" in bib_type:
            data["institution"] = data["publisher"]

        return data

    def get_bibtex_url(self) -> Optional[str]:
        if "pdf_url" in self.ctx.data:
            url = self.uri.replace("document", "bibtex")
            self.logger.debug("Using BibTeX URL: '%s'.", url)
            return url
        else:
            return None
