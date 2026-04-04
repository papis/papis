from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from papis.document import Document


def exporter(documents: list[Document]) -> str:
    """Convert document to the JSON format."""
    from papis.document import to_dict
    return json.dumps([to_dict(doc) for doc in documents],
                      sort_keys=True,
                      indent=2)
