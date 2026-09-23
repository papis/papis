"""YAML content-format handler."""

from __future__ import annotations

from io import StringIO

import yaml

from papis.sources.handler import ParseOutput
from papis.sources.handlers.formats import ContentFormatHandler
from papis.yaml import Loader  # type: ignore[attr-defined]


class YamlHandler(ContentFormatHandler):
    """Parse YAML content."""

    name = "yaml"

    @classmethod
    def parse(cls, content: str) -> ParseOutput | None:
        try:
            loaded = list(yaml.load_all(StringIO(content), Loader=Loader))
            documents = [doc for doc in loaded if isinstance(doc, dict)]

            message = None
            dropped = len(loaded) - len(documents)
            if dropped:
                message = f"{dropped} non-dict document(s) ignored."

            return ParseOutput(documents=documents, message=message)
        except Exception:
            return None
