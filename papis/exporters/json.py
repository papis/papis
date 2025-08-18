import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import papis.document


def exporter(documents: list["papis.document.Document"]) -> str:
    """Convert document to the JSON format."""
    from papis.document import to_dict
    return json.dumps([to_dict(doc) for doc in documents],
                      sort_keys=True,
                      indent=2)
