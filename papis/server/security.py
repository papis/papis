from __future__ import annotations

from typing import TYPE_CHECKING

from papis.server import exceptions as api_e

if TYPE_CHECKING:
    from pathlib import Path


def ensure_within_root(path: Path, root: Path) -> Path:
    """Ensure path resolves within root, raising on escape attempts.

    This is a security measure to prevent path traversal attacks (e.g., using
    ``..`` components or symlinks pointing outside the root).

    :param path: The path to validate.
    :param root: The root directory the path must stay within.
    :returns: The resolved path if it's within root.
    :raises HTTPException: 400 if path escapes root.
    """
    root_resolved = root.resolve()
    resolved = path.resolve()

    if not resolved.is_relative_to(root_resolved):
        raise api_e.PathEscapeError(f"Path '{path}' escapes directory '{root}'")

    return resolved
