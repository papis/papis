"""API exception classes and error codes.

All exceptions inherit from :class:`APIError` (which extends FastAPI's
:class:`HTTPException`).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

import papis.logging
from papis.server.models import ErrorDetail, ErrorResponse

logger = papis.logging.get_logger(__name__)


class APIError(HTTPException):
    """Base class for API errors.

    All subclasses produce a structured ``detail`` dict (an :class:`ErrorDetail`).
    Subclasses declare their HTTP status code. Each instance carries a
    machine-readable ``code`` string that clients use to distinguish error
    conditions.
    """

    status_code: int
    description: str = "Error"

    def __init__(
        self,
        message: str = "",
        *,
        code: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        detail = ErrorDetail(
            code=code,
            message=message,
            context=context,
        ).model_dump(exclude_none=True)
        super().__init__(
            status_code=self.status_code,
            detail=detail,
        )

    @classmethod
    def responses(
        cls, codes: list[str] | None = None
    ) -> dict[str | int, dict[str, Any]]:
        description = cls.description
        if codes:
            description += ". ``code`` is one of: " + ", ".join(codes)
        return {
            cls.status_code: {
                "model": ErrorResponse,
                "description": description,
            }
        }


class ErrorCode:
    # 400
    INVALID_JSON = "invalid_json"
    PATH_ESCAPE = "path_escape"
    FILES_IN_METADATA_NOT_ALLOWED = "read_only_field"
    READ_ONLY_FIELD = "read_only_field"
    INVALID_URI = "invalid_uri"
    IMPORTER_NO_DATA = "importer_no_data"
    MUTUALLY_EXCLUSIVE = "mutually_exclusive"
    UNKNOWN_EXPORT_FORMAT = "unknown_export_format"
    CITATION_NO_DOI = "citation_no_doi"
    CITATION_FETCH_EMPTY = "citation_fetch_empty"
    LOCAL_MODE_REQUIRED = "local_mode_required"
    # 404
    LIBRARY_NOT_FOUND = "library_not_found"
    DOCUMENT_NOT_FOUND = "document_not_found"
    FILE_NOT_FOUND = "file_not_found"
    NOTE_NOT_FOUND = "note_not_found"
    IMPORTER_NOT_FOUND = "importer_not_found"
    CHECK_NOT_FOUND = "check_not_found"
    # 409
    NOTES_EXIST = "notes_exist"
    # 412
    NOT_A_GIT_REPOSITORY = "not_a_git_repository"
    # 502
    UPSTREAM_ERROR = "upstream_error"
    # 500 (internal, only used in the catch-all handler)
    INTERNAL_SERVER_ERROR = "internal_server_error"


class BadRequestError(APIError):
    """Bad request (HTTP 400)."""

    status_code = 400
    description = "Bad request"


class ResourceNotFoundError(APIError):
    """Resource not found (HTTP 404)."""

    status_code = 404
    description = "Resource not found"


class ConflictError(APIError):
    """Conflict (HTTP 409)."""

    status_code = 409
    description = "Conflict"


class PreconditionFailedError(APIError):
    """Precondition failed (HTTP 412)."""

    status_code = 412
    description = "Precondition failed"


class InternalServerError(APIError):
    """Internal server error (HTTP 500)."""

    status_code = 500
    description = "Internal server error"


class UpstreamError(APIError):
    """Upstream error (HTTP 502)."""

    status_code = 502
    description = "Upstream error"


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI application.

    This installs a catch-all handler for all exceptions that aren't explicitly
    handled by the FastAPI server.
    """

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled exception in request %s %s: %r",
            request.method,
            request.url,
            exc,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": InternalServerError(
                    "Internal server error. The database may be in a bad state."
                    " Try running 'papis doctor' to diagnose.",
                    code=ErrorCode.INTERNAL_SERVER_ERROR,
                ).detail
            },
        )
