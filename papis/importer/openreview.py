from __future__ import annotations

import os
import re
from typing import Any

from openreview.api import Note, OpenReviewClient

from papis.document import split_authors_name
from papis.importer import Importer


class OpenReviewImporter(Importer):
    """Importer from Openreview URLs"""

    def __init__(self, uri: str) -> None:
        super().__init__(name="openreview", uri=uri)
        self.client = OpenReviewClient(baseurl="https://api2.openreview.net/")

    @classmethod
    def match(cls, uri: str) -> OpenReviewImporter | None:
        if re.search(r"openreview\.net/forum\?id=([^&]+)", uri):
            return OpenReviewImporter(uri)
        return None

    @staticmethod
    def _parse_note(note: Note) -> dict[str, Any]:
        """Extract data fields"""
        data = {}

        data["title"] = note.content.get("title", {}).get("value", "")
        data["abstract"] = note.content.get("abstract", {}).get("value", "")
        authors = note.content.get("authors", {}).get("value", [])
        data["author_list"] = split_authors_name(authors)

        bibtex = note.content.get("_bibtex", {}).get("value", "")

        # Extract year
        year_match = re.search(r"year=\{(\d+)\}", bibtex)
        if year_match:
            data["year"] = year_match.group(1)

        # Extract venue/journal
        booktitle_match = re.search(r"booktitle=\{([^}]+)\}", bibtex)
        if booktitle_match:
            data["booktitle"] = booktitle_match.group(1)
            data["type"] = "inproceedings"
        else:
            journal_match = re.search(r"journal=\{([^}]+)\}", bibtex)
            if journal_match:
                data["journal"] = journal_match.group(1)
                data["type"] = "article"

        url_match = re.search(r"url=\{([^}]+)\}", bibtex)
        if url_match:
            data["url"] = url_match.group(1)

        return data

    def fetch_data(self) -> None:
        match = re.search(r"openreview\.net/forum\?id=([^&]+)", self.uri)

        note_id = match.group(1)
        try:
            note = self.client.get_note(note_id)
            data = self._parse_note(note)

            data["openreview_id"] = note_id

            self.ctx.data = data.copy()

        except Exception as exc:
            self.logger.error(
                "Failed to download metadata from OpenReview.", exc_info=exc
            )

    def fetch_files(self) -> None:
        match = re.search(r"openreview\.net/forum\?id=([^&]+)", self.uri)

        note_id = match.group(1)
        try:
            import tempfile

            temp_dir = tempfile.mkdtemp()
            pdf_binary = self.client.get_attachment(id=note_id, field_name="pdf")
            filename = f"{note_id}.pdf"
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, "wb") as f:
                f.write(pdf_binary)

            self.ctx.files = [filepath]

        except Exception as exc:
            self.logger.error(
                "Failed to download paper from OpenReview.", exc_info=exc
            )

