import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)


def exporter(documents: list[papis.document.Document]) -> str:
    """Convert document to the JSON format"""
    import json
    return json.dumps([papis.document.to_dict(doc) for doc in documents],
                      sort_keys=True, indent=2)
