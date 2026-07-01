from __future__ import annotations

import pathlib
from typing import Annotated

from fastapi import APIRouter, Path

import papis.config
import papis.exceptions
from papis.server import exceptions as api_e
from papis.server.api import API_V1
from papis.server.models import LibraryResponse

router = APIRouter(prefix=API_V1)


def get_library_info(library: str) -> tuple[str, pathlib.Path]:
    """Get library information from the library name."""
    try:
        lib = papis.config.get_lib_from_name(library)
    except papis.exceptions.InvalidLibraryError as e:
        raise api_e.ResourceNotFoundError(f"Library '{library}' not found") from e
    return lib.name, pathlib.Path(
        lib.paths[0]
    )  # NOTE: simplify once we only support single path


@router.get("/libraries", tags=["Libraries"])
def list_libraries() -> list[LibraryResponse]:
    """Get information about all libraries."""
    names = papis.config.get_libs()
    return [LibraryResponse(name=name) for name in names]


@router.get("/libraries/{library}", tags=["Libraries"])
def get_library(
    library: Annotated[str, Path(description="Library name")],
) -> LibraryResponse:
    """Get information about a specific library."""
    lib_name, _ = get_library_info(library)
    return LibraryResponse(name=lib_name)
