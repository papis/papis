"""Configuration endpoint.

Path-like and tool-executable keys are filtered out for security.
"""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import Path

from papis import config as papis_config
from papis.server import exceptions
from papis.server.models import ConfigResponse
from papis.server.routes.libraries import library_router
from papis.strings import FormatPattern

# These might expose paths on the server
_UNSAFE_OPTIONS: frozenset[str] = frozenset({
    # Filesystem paths
    "cache-dir",
    "dir",
    "dirs",
    "header-format-file",
    "local-config-file",
    "notes-template",
    # bibtex
    "default-read-bibfile",
    "default-save-bibfile",
    # Tool executables
    "browser",
    "editor",
    "file-browser",
    "fzf-binary",
    "mark-opener-format",
    "mvtool",
    "opentool",
    "picktool",
})


def _build_sections() -> dict[str, dict[str, object]]:
    """Build the config sections dictionary for the current library.

    :return: A dict mapping section names to their key-value dicts, with
        path-like keys removed.
    """
    defaults = papis_config.get_default_settings()
    result: dict[str, dict[str, object]] = {}

    for section in defaults:
        section_dict: dict[str, object] = {}
        for key in defaults[section]:
            if (
                not papis_config.getboolean("server-local-mode")
                and key in _UNSAFE_OPTIONS
            ):
                continue
            value = papis_config.get(key, section=section)
            if value is not None:
                if isinstance(value, FormatPattern):
                    section_dict[key] = {
                        "__format_pattern__": [value.formatter, value.pattern]
                    }
                else:
                    try:
                        json.dumps(value)
                        section_dict[key] = value
                    except TypeError:
                        # Skip non-serializable types (e.g. `object()` sentinels).
                        continue
        result[section] = section_dict

    return result


@library_router.get(
    "/config",
    tags=["Configuration"],
    response_model=ConfigResponse,
    responses=exceptions.ResourceNotFoundError.responses(
        types=[exceptions.ErrorCode.LIBRARY_NOT_FOUND]
    ),
)
async def get_configuration(
    library: Annotated[str, Path(description="Library name")],
) -> ConfigResponse:
    """Return configuration for a library, grouped by section.

    Filesystem-path and tool-executable options are omitted unless the server is running
    in local mode.

    ``FormatPattern`` values (such as ``add-folder-name``) are serialised as
    ``{"__format_pattern__": [<formatter>, <pattern>]}``.
    """
    return ConfigResponse(sections=_build_sections())
