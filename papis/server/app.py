from __future__ import annotations

from fastapi import FastAPI

from papis.server.routes import (
    cache,
    documents,
    exporters,
    files,
    importers,
    libraries,
    notes,
)

app = FastAPI(
    title="Papis Server",
    description="REST API for Papis",
    version="v1",
)

app.include_router(libraries.router)
app.include_router(exporters.router)
app.include_router(importers.router)
app.include_router(documents.router)
app.include_router(files.router)
app.include_router(notes.router)
app.include_router(cache.router)
