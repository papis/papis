"""IEEE source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, ClassVar

from papis.exceptions import SourceError
from papis.sources.handler import FileReference, LookupOutput, SourceHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput

_PREFIX_RE = re.compile(r"^ieee:(\d+)$", re.IGNORECASE)
#: Document identifier in an IEEE Xplore URL, e.g. ``.../document/12345678``.
_URL_RE = re.compile(r"ieeexplore\.ieee\.org/document/(\d+)(?:[/?#]|$)")
_BIBTEX_URL = "https://ieeexplore.ieee.org/rest/search/citation/format"
_FILE_URL = (
    "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&isnumber=&arnumber={id}"
)


class IEEEHandler(SourceHandler):
    """Retrieve documents from IEEE Xplore <https://ieeexplore.ieee.org>."""

    name = "ieee"
    priority: ClassVar[int] = 10

    def __init__(self, identifier: str) -> None:
        super().__init__()
        self.identifier = identifier

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> IEEEHandler | None:
        text = evidence.input

        m = _PREFIX_RE.match(text)
        if m:
            return cls(m.group(1))

        if re.match(r".*ieee\.org.*", text):
            # NOTE: only claim URLs that carry an identifier
            m = _URL_RE.search(re.sub(r"\.pdf.*$", "", text))
            if m:
                return cls(m.group(1))

        return None

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        import html
        import json

        from requests.exceptions import RequestException

        from papis.bibtex import bibtex_to_dict
        from papis.utils import get_session

        params = {
            "recordIds": self.identifier,
            "citations-format": "citation-abstract",
            "download-format": "download-bibtex",
        }
        headers = {
            "Referer": f"https://ieeexplore.ieee.org/document/{self.identifier}",
        }

        try:
            with get_session() as session:
                response = session.get(_BIBTEX_URL, params=params, headers=headers)
        except RequestException as exc:
            raise SourceError(f"Could not query IEEE: {exc}") from exc

        documents: list[dict[str, Any]] = []
        if response.ok:
            # NOTE: the export is JSON-wrapped BibTeX
            try:
                payload = json.loads(response.content.decode())
                bibtex_data = html.unescape(payload["data"])
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                UnicodeDecodeError,
            ) as exc:
                raise SourceError(f"Unexpected response from IEEE: {exc}") from exc

            documents = [dict(entry) for entry in bibtex_to_dict(bibtex_data)]
        else:
            try:
                payload = json.loads(response.content.decode())
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise SourceError(
                    f"Could not query IEEE: HTTP {response.status_code}"
                ) from exc

            # NOTE: A response with status code 500 and reason "Unknown" means the
            # document couldn't be found. This is `no_result` and we do not raise an
            # error in this case.
            if not (
                response.status_code == 500
                and isinstance(payload, dict)
                and payload.get("reason") == "Unknown"
            ):
                raise SourceError(f"Could not query IEEE: HTTP {response.status_code}")

        document = documents[0] if documents else None
        files: list[FileReference] = []
        if document is not None:
            files = [
                FileReference(url=_FILE_URL.format(id=self.identifier), extension="pdf")
            ]

        return LookupOutput(
            document=document,
            files=files,
        )
