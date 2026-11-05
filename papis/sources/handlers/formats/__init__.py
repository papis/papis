"""Source handlers that get metadata from content in various file formats."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar

from papis.sources.handler import LookupOutput, ParseOutput, SourceHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


class ContentFormatHandler(SourceHandler):
    """Base class for handlers that parse content in different file formats."""

    priority: ClassVar[int] = 12

    def __init__(self, parsed: ParseOutput) -> None:
        super().__init__()
        self.parsed = parsed

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> ContentFormatHandler | None:
        candidates: list[str] = []
        if evidence.content is not None and evidence.kind == "file":
            candidates.append(evidence.content)
        candidates.append(evidence.input)

        for candidate in candidates:
            parsed = cls.parse(candidate)
            if parsed is not None and parsed.documents:
                return cls(parsed)

        return None

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        documents = self.parsed.documents

        messages = []
        if self.parsed.message:
            messages.append(self.parsed.message)
        if len(documents) > 1:
            messages.append(
                f"The {self.name} content contains {len(documents)} entries. "
                "Picking the first one."
            )

        return LookupOutput(
            document=documents[0] if documents else None,
            message=" ".join(messages) if messages else None,
        )

    @classmethod
    @abstractmethod
    def parse(cls, content: str) -> ParseOutput | None:
        """Parse *content* into documents' metadata.

        Return ``None`` when the content is not the source handler's format.
        """
        raise NotImplementedError(
            f"handler '{cls.name}' does not implement content parsing"
        )


__all__ = ["ContentFormatHandler"]
