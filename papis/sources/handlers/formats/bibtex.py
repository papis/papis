"""BibTeX content-format handler."""

from __future__ import annotations

from papis.bibtex import bibtex_to_dict
from papis.sources.handler import ParseOutput
from papis.sources.handlers.formats import ContentFormatHandler


class BibTeXHandler(ContentFormatHandler):
    """Parse BibTeX content."""

    name = "bibtex"

    @classmethod
    def parse(cls, content: str) -> ParseOutput | None:
        # NOTE: Due to a ``bibtexparser`` v1 limitation, this parser cannot distinguish
        # between content of the wrong format and correct but empty content. Hence, even
        # malformed content results in an empty list (``no_result``).
        try:
            return ParseOutput(
                documents=[dict(entry) for entry in bibtex_to_dict(content)],
            )
        except Exception:
            return None
