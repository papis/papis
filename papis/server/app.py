"""FastAPI application factory and top-level router setup."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import APIRouter, FastAPI

import papis.config
import papis.database
import papis.logging

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from papis.server.events import EventBroker, make_db_callback
from papis.server.exceptions import register_exception_handlers
from papis.server.routes import (
    cache,
    citations,
    config,
    doctor,
    documents,
    events,
    export,
    files,
    health,
    importers,
    libraries,
    notes,
)

VERSION = "v1"
PREFIX = f"/api/{VERSION}"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    os.environ["PAPIS_NP"] = "0"
    app.state.broker = EventBroker()
    watcher_tasks: list[asyncio.Task[None]] = []
    for lib_name in papis.config.get_libs():
        papis.config.set_lib_from_name(lib_name)

        # Set up events handling
        db = papis.database.get(lib_name)
        db.set_on_change_callback(make_db_callback(lib_name, app.state.broker))
    try:
        yield
    finally:
        for task in watcher_tasks:
            task.cancel()
        await asyncio.gather(*watcher_tasks, return_exceptions=True)


_API_DESCRIPTION = """
REST API for Papis

Notes
-----

**Local mode:** The ``server-local-mode`` option indicates to the server that the client
is running on the same host. This unlocks various functionalities that are noted in the
endpoint documentations.

**Paths:** All returned paths use POSIX forward-slash separators.

**Error format:** All errors follow `RFC 7807 <https://tools.ietf.org/html/rfc7807>`_
(``application/problem+json``). The response body includes ``type`` (machine-readable
code), ``title`` (short summary), ``status`` (HTTP status), ``detail`` (human-readable
explanation), and optional ``context`` for structured data about the resources involved.

**Config overrides:** You can override options per request via
``X-Papis-Config-Override`` a header with the value ``{"section": {"key": "value"}}``.

**Format patterns:** Endpoints resolve format patterns when appropriate.

**Git:** All mutating endpoints allow using git to auto-commit changes.

**Concurrency:** Document responses include an ``ETag`` version. Mutating endpoints
accept (but do not require) an ``If-Match`` header to avoid editing resources that have
been mutated since the last read. A ``412`` response means the document changed since
the last read.

**Validation errors:** Any endpoint accepting a request body may return
``422 Unprocessable Content`` when Pydantic validation fails (wrong types, missing
required fields, etc.).

"""

app = FastAPI(
    title="Papis Server",
    description=_API_DESCRIPTION,
    version=VERSION,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Libraries", "description": "Manage libraries"},
        {"name": "Documents", "description": "Manage Documents"},
        {"name": "Document Files", "description": "Manage file attachments"},
        {"name": "Document Notes", "description": "Manage notes"},
        {"name": "Document Citations", "description": "Manage citations and cited-by"},
        {"name": "Export", "description": "Export documents"},
        {"name": "Import", "description": "Import metadata from external sources"},
        {"name": "Doctor", "description": "Run doctor checks"},
        {"name": "Configuration", "description": "Get library configuration"},
        {"name": "Cache", "description": "Cache management"},
        {"name": "Health", "description": "Check server health"},
    ],
)

router = APIRouter(prefix=PREFIX)
router.include_router(libraries.router)
router.include_router(libraries.library_router)
router.include_router(health.router)

app.include_router(router)

register_exception_handlers(app)
