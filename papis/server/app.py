"""FastAPI application factory and top-level router setup."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import APIRouter, FastAPI

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from papis.server.exceptions import register_exception_handlers
from papis.server.routes import (
    cache,
    citations,
    config,
    doctor,
    documents,
    export,
    files,
    health,
    importers,
    libraries,
    notes,
)

VERSION = "v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    os.environ["PAPIS_NP"] = "0"
    yield


app = FastAPI(
    title="Papis Server",
    description="REST API for Papis",
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
    ],
)

router = APIRouter(prefix=f"/api/{VERSION}")
router.include_router(libraries.router)
router.include_router(libraries.library_router)
router.include_router(health.router)

app.include_router(router)

register_exception_handlers(app)
