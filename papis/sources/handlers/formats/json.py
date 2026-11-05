"""JSON content-format handler."""

from __future__ import annotations

import json

from papis.sources.handler import ParseOutput
from papis.sources.handlers.formats import ContentFormatHandler


class JsonHandler(ContentFormatHandler):
    """Parse JSON content."""

    name = "json"

    @classmethod
    def parse(cls, content: str) -> ParseOutput | None:
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return ParseOutput(documents=[data])
            if isinstance(data, list):
                documents = [doc for doc in data if isinstance(doc, dict)]

                message = None
                dropped = len(data) - len(documents)
                if dropped:
                    message = f"{dropped} non-object element(s) ignored."

                return ParseOutput(
                    documents=documents, message=message
                )
            return ParseOutput()
        except Exception:
            return None
