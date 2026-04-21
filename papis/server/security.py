"""API security functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from papis.server import exceptions

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
        raise exceptions.BadRequestError(
            f"Path '{path}' escapes directory '{root}'",
            code=exceptions.ErrorCode.PATH_ESCAPE,
            context={"path": str(path)},
        )

    return resolved
