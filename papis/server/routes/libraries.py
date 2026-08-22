"""Library endpoints and context injection.

Provides the ``library_context`` FastAPI dependency that validates
the library name, scopes all subsequent config lookups to it,
and applies per-request ``X-Papis-Config-Override`` overrides.
"""

from __future__ import annotations

import json
import os
import pathlib
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, Header, Path, Request

if TYPE_CHECKING:
    from collections.abc import Generator

    from papis.database.base import Database

import papis.config
import papis.database
import papis.exceptions
from papis.server import exceptions
from papis.server.models import LibrariesResponse, LibraryResponse, SubfoldersResponse

router = APIRouter()

_UNSET_CONFIG_KEY = object()


def _apply_overrides(
    overrides: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Apply config overrides and return a snapshot for later restoration.

    :param overrides: mapping of section to key to new_value.
    :returns: mapping of section to key to old_value (or ``_UNSET_CONFIG_KEY``).
    """
    snapshot: dict[str, dict[str, Any]] = {}
    for section, settings in overrides.items():
        sec_snap: dict[str, Any] = {}
        for key, value in settings.items():
            try:
                sec_snap[key] = papis.config.get(key, section=section)
            except papis.exceptions.DefaultSettingValueMissing:
                sec_snap[key] = _UNSET_CONFIG_KEY
            papis.config.set(key, value, section=section)
        snapshot[section] = sec_snap
    return snapshot


def _restore_snapshot(snapshot: dict[str, dict[str, Any]]) -> None:
    """Restore config values from a snapshot.

    :param snapshot: mapping of section to key to old_value (or ``_UNSET_CONFIG_KEY``).
    """
    config = papis.config.get_configuration()
    for section, settings in snapshot.items():
        for key, value in settings.items():
            if value is _UNSET_CONFIG_KEY:
                if config.has_section(section):
                    config.remove_option(section, key)
            else:
                papis.config.set(key, value, section=section)


def _library_context(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    x_papis_config_override: Annotated[
        str | None,
        Header(
            alias="X-Papis-Config-Override",
            description=(
                'JSON-encoded ``{"<section>": {"<key>": "<value>"}}`` mapping.'
                " Scoped to a single request, never persisted."
            ),
        ),
    ] = None,
) -> Generator[None, None, None]:
    """Validate the library, apply per-request config overrides, then restore.

    Scopes all config lookups to *library*. If the request carries an
    ``X-Papis-Config-Override`` header, those values are applied before the handler runs
    and restored afterwards.

    Stores the library name and path on ``request.state`` (``lib_name`` and
    ``lib_path``) for downstream handlers.

    :param request: The incoming request.
    :param library: Name of the library.
    :param x_papis_config_override: Per-request config overrides (JSON).
    :raises ResourceNotFoundError: If the library does not exist.
    """
    try:
        lib = papis.config.get_lib_from_name(library)
    except papis.exceptions.InvalidLibraryError as e:
        raise exceptions.ResourceNotFoundError(
            f"Library '{library}' not found",
            type=exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            context={"library": library},
        ) from e
    request.state.lib_name = lib.name
    request.state.lib_path = pathlib.Path(lib.path).resolve()
    papis.config.set_lib_from_name(library)

    config_snapshot: dict[str, dict[str, Any]] | None = None
    if papis.config.getboolean("server-local-mode") and x_papis_config_override:
        try:
            overrides = json.loads(x_papis_config_override)
            if isinstance(overrides, dict):
                config_snapshot = _apply_overrides(overrides)
        except json.JSONDecodeError:
            pass  # We ignore malformed headers

    try:
        yield
    finally:
        if config_snapshot is not None:
            _restore_snapshot(config_snapshot)


library_router = APIRouter(
    prefix="/libraries/{library}",
    dependencies=[Depends(_library_context)],
)


def get_db(library: str) -> Database:
    """Get database for a library name.

    :param library: Name of the library.
    :return: The database instance.
    """
    return papis.database.get(library)


@router.get("/libraries", response_model=LibrariesResponse, tags=["Libraries"])
async def list_libraries() -> LibrariesResponse:
    """Get information about all libraries."""
    result: list[LibraryResponse] = []
    for name in papis.config.get_libs():
        path: str | None = None
        if papis.config.getboolean("server-local-mode"):
            path = pathlib.Path(papis.config.get_lib_from_name(name).path).as_posix()
        result.append(LibraryResponse(name=name, path=path))
    return LibrariesResponse(libraries=result)


@library_router.get(
    "",
    tags=["Libraries"],
    response_model=LibraryResponse,
    responses=exceptions.ResourceNotFoundError.responses(
        types=[exceptions.ErrorCode.LIBRARY_NOT_FOUND]
    ),
)
async def get_library_information(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
) -> LibraryResponse:
    """Get information about a specific library."""
    return LibraryResponse(
        name=request.state.lib_name,
        path=request.state.lib_path.as_posix()
        if papis.config.getboolean("server-local-mode")
        else None,
    )


@library_router.get(
    "/subfolders",
    tags=["Libraries"],
    response_model=SubfoldersResponse,
    responses=exceptions.ResourceNotFoundError.responses(
        types=[exceptions.ErrorCode.LIBRARY_NOT_FOUND]
    ),
)
async def list_subfolders(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
) -> SubfoldersResponse:
    """List subfolders within a library.

    Subfolders are folders within a library that aren't any document's folder. Hidden
    directories (names starting with ``.``) are skipped. The library root (``"."``) is
    always included. Results are sorted.
    """
    lib_path = request.state.lib_path
    info_name = papis.config.getstring("info-name")

    subfolders: set[str] = set()

    for dirpath_str, dirnames, _ in os.walk(lib_path):
        dirpath = pathlib.Path(dirpath_str)
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if not dirname.startswith(".")
            and not (dirpath / dirname / info_name).exists()
        ]
        rel = dirpath.relative_to(lib_path)
        subfolders.add(rel.as_posix())

    return SubfoldersResponse(subfolders=sorted(subfolders))
