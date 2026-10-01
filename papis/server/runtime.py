"""Server process runtime management."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import papis.config
import papis.logging

logger = papis.logging.get_logger(__name__)

_psutil: Any = None


def _ensure_psutil() -> None:
    """Import ``psutil`` on Windows, raising ``ImportError`` if absent."""
    if sys.platform != "win32":
        return
    global _psutil
    if _psutil is not None:
        return
    try:
        import psutil  # type: ignore[import-untyped,unused-ignore]

        _psutil = psutil
    except ImportError:
        raise ImportError(
            "The 'psutil' package is required for background server "
            "operations on Windows. Install it with: pip install psutil"
        ) from None


def get_pid_file() -> Path:
    """Get the path to the server PID file."""
    from papis.utils import get_cache_home

    return Path(get_cache_home()) / "papis-server.pid"


def pid_exists(pid: int) -> bool:
    """Check if a process with the given PID is currently running.

    :param pid: Process ID.
    :returns: ``True`` if the process is running.
    """
    if sys.platform == "win32":
        _ensure_psutil()
        return bool(_psutil.pid_exists(pid))

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def is_server_running_on_host() -> bool:
    """Check if a server process is currently running.

    Cleans up invalid or stale PID files.

    :returns: ``True`` if the PID file exists and the process is alive.
    """
    pid_file = get_pid_file()
    if not pid_file.exists():
        return False

    try:
        pid_str = pid_file.read_text().strip()
        pid = int(pid_str)
    except (ValueError, OSError):
        logger.debug("Invalid PID file at '%s'.", pid_file)
        pid_file.unlink(missing_ok=True)
        return False

    if not pid_exists(pid):
        logger.debug("Stale PID file (PID %s not running).", pid)
        pid_file.unlink(missing_ok=True)
        return False

    return True


def _reject_if_already_running() -> None:
    """Refuse to start a second server.

    :raises SystemExit: If a server is already running.
    """
    if not is_server_running_on_host():
        return

    pid_file = get_pid_file()
    try:
        pid: int | str = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        pid = "?"

    logger.error(
        "Server is already running (PID %s). Use 'papis server --stop' to stop it.",
        pid,
    )
    raise SystemExit(1) from None


def serve(url: str, *, background: bool = False) -> None:
    """Run the Papis server.

    Foreground (``background=False``): runs in the current process,
    blocks until interrupted.

    Background (``background=True``): spawns a detached child and
    returns immediately.

    :param url: URL to listen on (e.g. ``http://127.0.0.1:8383``).
    :param background: If ``True``, run in the background.
    """
    from urllib.parse import urlparse

    _reject_if_already_running()

    if background:
        args = [
            sys.executable,
            "-m",
            "papis",
            "server",
            "--server-url",
            url,
        ]

        kwargs: dict[str, Any] = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }

        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            if hasattr(subprocess, "DETACHED_PROCESS"):
                creationflags |= subprocess.DETACHED_PROCESS
            kwargs["creationflags"] = creationflags
        else:
            kwargs["start_new_session"] = True

        log_path = papis.config.get("server-log-file")
        if log_path:
            log_file = Path(log_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_fh = open(str(log_file), "a", encoding="utf-8")
            kwargs["stdout"] = log_fh
            kwargs["stderr"] = log_fh

        logger.info(
            "Starting background Papis server on %s.",
            url,
        )

        subprocess.Popen(args, **kwargs)
        return

    pid_file = get_pid_file()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))

    import uvicorn

    log_level = os.environ.get("PAPIS_LOG_LEVEL", "INFO").lower()

    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8383

    logger.info(
        "Starting Papis server on %s (log level: %s).",
        url,
        log_level,
    )
    logger.info(
        "Interactive Swagger documentation at %s/docs.",
        url,
    )
    logger.info(
        "Redoc documentation at %s/redoc.",
        url,
    )
    logger.info("Press Ctrl+C to stop the server.")

    try:
        uvicorn.run(
            "papis.server.app:app",
            host=host,
            port=port,
            log_level=log_level,
        )
    finally:
        pid_file.unlink(missing_ok=True)


def stop_server() -> None:
    """Stop a running background server.

    Sends ``SIGTERM`` to the process and waits for it to exit. If it
    does not exit, ``SIGKILL`` is sent.

    :raises SystemExit: If no PID file exists or the process is not running.
    """
    pid_file = get_pid_file()
    if not pid_file.exists():
        logger.error("No server PID file found. Is the server running?")
        raise SystemExit(1)

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        logger.error("Invalid PID file at '%s'.", pid_file)
        pid_file.unlink(missing_ok=True)
        raise SystemExit(1) from None

    if not pid_exists(pid):
        logger.warning(
            "Server process %s is not running. Removing stale PID file.", pid
        )
        pid_file.unlink(missing_ok=True)
        raise SystemExit(0) from None

    try:
        os.kill(pid, signal.SIGTERM)
    except PermissionError:
        logger.error("Server process %s is running but cannot be signaled.", pid)
        raise SystemExit(1) from None
    except (ProcessLookupError, OSError):
        pid_file.unlink(missing_ok=True)
        logger.info("Server stopped.")
        return

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if not pid_exists(pid):
            logger.info("Server stopped.")
            pid_file.unlink(missing_ok=True)
            return
        time.sleep(0.1)

    # ``SIGKILL`` is POSIX-only, but on Windows ``TerminateProcess`` kills
    # synchronously, so reaching here is impossible.
    if hasattr(signal, "SIGKILL"):
        logger.warning("Server did not stop gracefully. Sending SIGKILL.")
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    pid_file.unlink(missing_ok=True)
    logger.info("Server stopped.")
