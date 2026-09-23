"""HAL source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import papis.config
from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput

# NOTE: this only advertises subdomains maintained by CCSD
# https://www.ccsd.cnrs.fr/2022/06/hal-archives-ouvertes-fr-va-devenir-hal-science/

# TODO: a list of other domains seems to be available at
# https://hal.science/browse/portal

#: Subdomains maintained by CCSD
_SUBDOMAINS_ARCHIVES_OUVERTES = (
    "hal",
    "halshs",
    "tel",
    "medihal",
    # other domains
    "hal-anr",
    "hal-bnf",
    "hal-cea",
    "hal-centralesupelec",
    "hal-cnam",
    "hal-cnrs",
)

_SUBDOMAINS_SCIENCE = (
    "hal",
    r"shs\.hal",
    r"theses\.hal",
    r"media\.hal",
)

_URL_RE = re.compile(
    rf".*({'|'.join(_SUBDOMAINS_ARCHIVES_OUVERTES)})\.archives-ouvertes\.fr.*"
    rf"|.*//({'|'.join(_SUBDOMAINS_SCIENCE)})\.science.*",
    re.IGNORECASE,
)


class HALHandler(WebsiteHandler):
    """Retrieve documents from the `HAL <https://hal.science>`__ family of websites.

    Scrapes the page's meta headers and gets the page's BibTeX URL when the page
    has a PDF.
    """

    name = "hal"
    url_or_id_re = _URL_RE

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data = super().scrape(evidence)

        if data:
            if "url" not in data:
                data["url"] = evidence.input

            keywords = data.get("keywords")
            if keywords is not None:
                # FIXME: also add to `tags`?
                data["keywords"] = [kw.strip() for kw in keywords.split(";")]

            bib_type = data.get("type")
            if bib_type is not None and "thesis" in bib_type:
                data["institution"] = data["publisher"]

        return data

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        doc_url: str | None = self.data.get(papis.config.getstring("doc-url-key-name"))
        if not doc_url or not doc_url.endswith("/document"):
            return None

        return doc_url.removesuffix("/document") + "/bibtex"
