"""API exception classes and error codes.

All exceptions inherit from :class:`APIError` (which extends FastAPI's
:class:`HTTPException`).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import papis.logging
from papis.server.models import ProblemResponse

logger = papis.logging.get_logger(__name__)


class APIError(HTTPException):
    """Base class for API errors.

    Errors are returned as `RFC 7807 <https://tools.ietf.org/html/rfc7807>`_ problem
    detail objects. Subclasses declare their HTTP status code and a short ``title``.
    Each instance carries a machine-readable ``type`` that clients may use to
    distinguish error conditions.
    """

    status_code: int
    title: str = "Error"

    def __init__(
        self,
        detail: str = "",
        *,
        type: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.problem = ProblemResponse(
            type=type,
            title=self.title,
            status=self.status_code,
            detail=detail,
            context=context,
        )
        super().__init__(
            status_code=self.status_code,
            detail=self.problem.model_dump(exclude_none=True),
        )

    @classmethod
    def responses(
        cls, types: list[str] | None = None
    ) -> dict[str | int, dict[str, Any]]:
        title_str = cls.title
        if types:
            title_str += ". ``type`` is one of: " + ", ".join(types)
        return {
            cls.status_code: {
                "model": ProblemResponse,
                "description": title_str,
            }
        }


class ErrorCode:
    # 400
    INVALID_JSON = "/errors/invalid-json"
    PATH_ESCAPE = "/errors/path-escape"
    IMMUTABLE_FIELD = "/errors/immutable-field"
    INVALID_URI = "/errors/invalid-uri"
    IMPORTER_NO_DATA = "/errors/importer-no-data"
    MISSING_FIELD = "/errors/missing-field"
    MUTUALLY_EXCLUSIVE = "/errors/mutually-exclusive"
    UNKNOWN_EXPORT_FORMAT = "/errors/unknown-export-format"
    CITATION_NO_DOI = "/errors/citation-no-doi"
    CITATION_FETCH_EMPTY = "/errors/citation-fetch-empty"
    LOCAL_MODE_REQUIRED = "/errors/local-mode-required"
    VALIDATION_ERROR = "/errors/validation-error"
    # 404
    LIBRARY_NOT_FOUND = "/errors/library-not-found"
    DOCUMENT_NOT_FOUND = "/errors/document-not-found"
    FILE_NOT_FOUND = "/errors/file-not-found"
    NOTE_NOT_FOUND = "/errors/note-not-found"
    IMPORTER_NOT_FOUND = "/errors/importer-not-found"
    CHECK_NOT_FOUND = "/errors/check-not-found"
    # 409
    NOTES_EXIST = "/errors/notes-exist"
    FOLDER_EXISTS = "/errors/folder-exists"
    FOLDER_INSIDE_DOCUMENT = "/errors/folder-inside-document"
    FILE_EXISTS = "/errors/file-exists"
    # 412
    NOT_A_GIT_REPOSITORY = "/errors/not-a-git-repository"
    VERSION_MISMATCH = "/errors/version-mismatch"
    # 502
    UPSTREAM_ERROR = "/errors/upstream-error"
    # 500 (internal, only used in the catch-all handler)
    INTERNAL_SERVER_ERROR = "/errors/internal-server-error"


class BadRequestError(APIError):
    """Bad request (HTTP 400)."""

    status_code = 400
    title = "Bad request"


class ResourceNotFoundError(APIError):
    """Resource not found (HTTP 404)."""

    status_code = 404
    title = "Resource not found"


class ConflictError(APIError):
    """Conflict (HTTP 409)."""

    status_code = 409
    title = "Conflict"


class PreconditionFailedError(APIError):
    """Precondition failed (HTTP 412)."""

    status_code = 412
    title = "Precondition failed"


class InternalServerError(APIError):
    """Internal server error (HTTP 500)."""

    status_code = 500
    title = "Internal server error"


class UpstreamError(APIError):
    """Upstream error (HTTP 502)."""

    status_code = 502
    title = "Upstream error"


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI application.

    Installs an :class:`APIError` handler that returns ``application/problem+json``
    (RFC 7807), normalises ``RequestValidationError`` to the same format, and adds a
    catch-all for unhandled exceptions.
    """

    @app.exception_handler(APIError)
    async def api_error_handler(_request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.problem.model_dump(exclude_none=True),
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        detail = "; ".join(
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in errors
        )
        return JSONResponse(
            status_code=422,
            content=ProblemResponse(
                type=ErrorCode.VALIDATION_ERROR,
                title="Validation error",
                status=422,
                detail=detail,
                context={"errors": errors},
            ).model_dump(exclude_none=True),
            media_type="application/problem+json",
        )

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
            content=InternalServerError(
                "Internal server error. The database may be in a bad state."
                " Try running 'papis doctor' to diagnose.",
                type=ErrorCode.INTERNAL_SERVER_ERROR,
            ).problem.model_dump(exclude_none=True),
            media_type="application/problem+json",
        )
