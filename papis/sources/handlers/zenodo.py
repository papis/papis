"""Zenodo source handler."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import papis.zenodo
from papis.sources.handler import FileReference, LookupOutput, SourceHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


class ZenodoHandler(SourceHandler):
    """Retrieve documents and files for a Zenodo record ID."""

    name = "zenodo"

    def __init__(self, record_id: str) -> None:
        super().__init__()
        self.record_id = record_id

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> ZenodoHandler | None:
        candidate = evidence.input
        if not candidate.isdigit():
            return None

        # NOTE: a 978/979 ISBN-13 is never a Zenodo record ID, so don't query.
        if len(candidate) == 13 and candidate.startswith(("978", "979")):
            return None

        return cls(candidate)

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        data = papis.zenodo.get_data(self.record_id)
        document = None
        files: list[FileReference] = []
        if data:
            document = papis.zenodo.zenodo_data_to_papis_data(data)
            files = [
                FileReference(
                    url=file["links"]["self"],
                    filename=file["key"],
                    extension=os.path.splitext(file["key"])[1].lstrip(".") or None,
                )
                for file in data.get("files", [])
            ]

        return LookupOutput(
            document=document,
            files=files,
        )
