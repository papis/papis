from __future__ import annotations

from typing import Any

from fastapi import HTTPException


class ApiError(HTTPException):
    """Base class for API errors.

    Can be used to raise exceptions and to create OpenAPI docs.
    """

    status_code: int
    description: str = "Error"

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=self.status_code, detail=detail)

    @classmethod
    def responses(cls) -> dict[str | int, dict[str, Any]]:
        return {cls.status_code: {"description": cls.description}}


# =============================================================================
# 400
# =============================================================================


class BadRequestError(ApiError):
    status_code = 400
    description = "Bad request"


class PathEscapeError(ApiError):
    status_code = 400
    description = "Path escapes the allowed root"


class FilesNotAllowedError(ApiError):
    status_code = 400
    description = "Files and notes must be managed via their endpoints"


class FilenameRequiredError(ApiError):
    status_code = 400
    description = "Filename is required"


class InvalidURIError(ApiError):
    status_code = 400
    description = "Invalid URI or importer cannot handle it"


class ImporterNoDataError(ApiError):
    status_code = 400
    description = "Importer returned no data"


class UnknownExportFormat(ApiError):
    status_code = 400
    description = "Unknown export format"


# =============================================================================
# 404
# =============================================================================


class ResourceNotFoundError(ApiError):
    status_code = 404
    description = "Resource not found"


# =============================================================================
# 409
# =============================================================================


class NotesExistError(ApiError):
    status_code = 409
    description = "Document already has notes"


# =============================================================================
# 502
# =============================================================================


class UpstreamError(ApiError):
    status_code = 502
    description = "Failed to fetch data from upstream source"
