from __future__ import annotations

from typing import TYPE_CHECKING

import papis.config
import papis.logging

if TYPE_CHECKING:
    from papis.document import Document

logger = papis.logging.get_logger(__name__)


def exporter(documents: list[Document]) -> str:
    """Convert documents to the CSV format"""

    delimiter = papis.config.get("exporter-csv-delimiter")
    if delimiter is None:
        delimiter = ","
    delimiter = delimiter.strip(" '\"")

    if not delimiter:
        logger.warning(
            "Invalid delimiter %r. Expected one character -- falling back to ','.",
            delimiter
        )
        delimiter = ","

    dialect = papis.config.get("exporter-csv-dialect")
    if dialect is None:
        dialect = "excel"
    dialect = dialect.lower()

    keys = papis.config.getlist("exporter-csv-keys")
    if not keys:
        from papis.bibtex import bibtex_keys
        keys = list(bibtex_keys)

    keys.extend(papis.config.getlist("exporter-csv-keys-extend"))

    import csv
    import io

    dialects = csv.list_dialects()
    if dialect not in dialects:
        logger.error(
            "Unknown CSV dialect '%s'. Available dialects are '%s' (using 'excel').",
            dialect, "', '".join(dialects),
        )
        dialect = "excel"

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=keys,
        dialect=dialect,
        delimiter=delimiter,
        quoting=csv.QUOTE_NONNUMERIC,
    )
    writer.writeheader()

    from papis.document import author_list_to_author

    au_separator = papis.config.getstring("multiple-authors-separator")
    au_format = papis.config.getformatpattern("multiple-authors-format")

    for doc in documents:
        row = {}
        for key in keys:
            if key in {"author", "author_list"}:
                row[key] = author_list_to_author(
                    doc, separator=au_separator, multiple_authors_format=au_format
                )
            else:
                value = doc.get(key)
                if value is None:
                    value = ""
                if isinstance(value, list):
                    value = "; ".join(str(item) for item in value)
                else:
                    value = str(value)

                row[key] = value

        writer.writerow(row)

    return buffer.getvalue()
