import os
from contextlib import suppress
from typing import Any, Dict, List, Optional

from citeproc.source import BibliographySource, Date, Name, Reference
from citeproc.source.bibtex import BibTeX

import papis.config
import papis.logging
from papis.document import Document

logger = papis.logging.get_logger(__name__)

#: URL from which to download styles from if not available locally.
ZOTERO_CSL_STYLE_URL = "https://www.zotero.org/styles/{}"

#: Subfolder in the Papis configuration folder where styles are stored.
CSL_STYLES_FOLDER = "styles"


def get_styles_folder() -> str:
    return os.path.join(papis.config.get_config_folder(), CSL_STYLES_FOLDER)


def _download_style(name: str) -> None:
    if name.endswith(".csl"):
        name = name[:-4]

    styles_folder = get_styles_folder()
    style_path = os.path.join(styles_folder, f"{name}.csl")
    if os.path.exists(style_path):
        return

    from papis.utils import get_session

    with get_session() as session:
        response = session.get(ZOTERO_CSL_STYLE_URL.format(name),
                               allow_redirects=True)

    if not response.ok:
        logger.error("Could not download style '%s'. (HTTPS status: %s %d)",
                     name, response.reason, response.status_code)
        return

    if not os.path.exists(styles_folder):
        os.mkdir(styles_folder)

    with open(style_path, mode="wb") as fout:
        fout.write(response.content)

    logger.info("Style '%s' downloaded to '%s'.", name, style_path)


def _parse_date(doc: Document) -> Optional[Date]:
    """Extract a date from a document."""

    if "year" not in doc:
        return None

    try:
        year = int(doc["year"])
    except ValueError:
        return None

    date = {"year": year}
    if "month" in doc:
        month = doc["month"]
        if isinstance(month, int):
            if 1 <= month <= 12:
                date["month"] = month
        elif isinstance(month, str):
            month = month.strip().lower()
            try:
                date["month"] = BibTeX.MONTHS.index(month[:3]) + 1
            except ValueError:
                try:
                    date["month"] = int(month)
                except ValueError:
                    pass

    return Date(**date)


def to_csl(doc: Document) -> Dict[str, Any]:
    """Convert a document into a dictionary of keys supported by :mod:`citeproc`.

    This function only converts keys that are supported, while other keys in the
    document are ignored.
    """

    # FIXME: we're using the fields from citeproc to make sure that we're
    # compatible with their CSL spec, but ideally this would map all BibTeX fields
    known_fields = BibTeX.fields

    result = {}
    for key, value in doc.items():
        csl_key = known_fields.get(key)
        if csl_key is None:
            continue

        csl_value: Any
        if key in {"number", "volume"}:
            with suppress(ValueError):
                csl_value = int(value)
        elif key == "pages":
            # NOTE: this just tries to remove any double dashes from the pages
            csl_value = "-".join([
                p for page in value.split("-") if (p := page.strip())
                ])
        elif key == "author":
            # FIXME: CSL supports the full 'first + von + last + jr' split naming
            csl_value = [
                Name(given=author["given"], family=author["family"])
                for author in doc["author_list"]
            ]
        else:
            # FIXME: citeproc seems to have some notion of MixedString that
            # allows keeping some words capitalized. We don't have that..
            csl_value = str(value)

        result[csl_key] = csl_value

    date = _parse_date(doc)
    if date is not None:
        result["issued"] = date

    return result


class PapisSource(BibliographySource):  # type: ignore[misc]
    def __init__(self, doc: Document) -> None:
        super().__init__()

        csl_type = BibTeX.types.get(doc["type"], BibTeX.types["misc"])
        csl_fields = to_csl(doc)
        self.add(Reference(doc["ref"].lower(), csl_type, **csl_fields))


def normalize_style_path(name: str) -> str:
    name = os.path.basename(name)
    if name.endswith(".csl"):
        name = name[:-4]

    from citeproc import STYLES_PATH

    style_path = os.path.join(STYLES_PATH, f"{name}.csl")
    if os.path.exists(style_path):
        return style_path

    style_path = os.path.join(get_styles_folder(), f"{name}.csl")
    if os.path.exists(style_path):
        return style_path

    _download_style(name)
    if os.path.exists(style_path):
        return style_path

    return ""


def export_document(doc: Document,
                    style_name: Optional[str] = None,
                    formatter_name: Optional[str] = None) -> str:
    if style_name is None:
        style_name = papis.config.getstring("csl-style")

    if formatter_name is None:
        formatter_name = papis.config.getstring("csl-formatter")

    style_name = os.path.normpath(os.path.expanduser(style_name))
    if not os.path.isabs(style_name):
        style_name = normalize_style_path(style_name)

    if not os.path.exists(style_name):
        logger.error("Cannot find style '%s'. You can download or create this "
                     "style yourself and place it in '%s'.",
                     os.path.basename(style_name), get_styles_folder())
        return ""

    from citeproc import CitationStylesStyle

    source = PapisSource(doc)
    style = CitationStylesStyle(style_name, validate=False)

    from citeproc import CitationStylesBibliography, Citation, CitationItem, formatter

    fmt = getattr(formatter, formatter_name, None)
    if fmt is None:
        logger.error("Formatter '%s' is not supported for CSL export. "
                     "Check your 'csl-formatter' setting in the configuration file.",
                     formatter_name)
        return ""

    bib = CitationStylesBibliography(style, source, fmt)
    citation = Citation([CitationItem(doc["ref"])])
    bib.register(citation)

    # TODO: the citeproc example says we should strive to cite all the documents
    # at once, since some of the formatting may depend on the previous citations
    def warn(item: CitationItem) -> None:
        logger.warning("Reference with key '%s' not found in the bibliography",
                       item.key)

    bib.cite(citation, callback=warn)

    try:
        for item in bib.bibliography():
            return str(item).replace("..", ".")
    except AttributeError as exc:
        # NOTE: citeproc-py doesn't support all known styles, so the export can fail
        logger.error("Failed to export citation '%s' to CSL style '%s'.",
                     doc["ref"], os.path.basename(style_name), exc_info=exc)

    return ""


def exporter(documents: List[Document]) -> str:
    formatter_name = papis.config.getstring("csl-formatter")
    style_name = papis.config.getstring("csl-style")

    return "\n\n".join(
        export_document(doc, style_name=style_name, formatter_name=formatter_name)
        for doc in documents
    ).strip()
