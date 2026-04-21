from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Response

import papis.api
from papis.server.api import API_V1
from papis.server.routes.libraries import get_library_info

router = APIRouter(prefix=API_V1)


@router.delete("/libraries/{library}/cache", tags=["Cache"])
def clear_cache(library: Annotated[str, Path(description="Library name")]) -> Response:
    """Clear the document cache for a library."""
    _, _ = get_library_info(library)
    papis.api.clear_lib_cache(library)
    return Response(status_code=204)
