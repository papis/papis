from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import papis.document


def exporter(documents: list["papis.document.Document"]) -> str:
    """Convert document to the YAML format."""
    import yaml

    from papis.document import to_dict

    string = yaml.dump_all(
        [to_dict(document) for document in documents],
        allow_unicode=True)

    return str(string)
