"""
The ``server`` command starts the Papis API server.

The server exposes a JSON REST API for managing libraries.

Examples
^^^^^^^^

- Start the server on the default host and port:

    .. code:: sh

        papis server

- Start the server bound to all interfaces on a custom port:

    .. code:: sh

        papis server --host 0.0.0.0 --port 9000

- Start the server in the background:

    .. code:: sh

        papis server --background

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.server:cli
    :prog: papis server
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any

import click
import uvicorn

import papis.cli
import papis.config
import papis.logging

if TYPE_CHECKING:
    from pathlib import Path

logger = papis.logging.get_logger(__name__)


def _get_pid_file() -> Path:
    """Get the path to the server PID file."""
    from pathlib import Path

    from papis.utils import get_cache_home

    return Path(get_cache_home()) / "papis-server.pid"


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


def _pid_exists(pid: int) -> bool:
    """Return ``True`` if a process with *pid* is currently running."""
    if sys.platform == "win32":
        return bool(_psutil.pid_exists(pid))

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _daemonize(port: int, host: str) -> None:
    """Daemonize the current process.

    On Unix this uses double-fork. On Windows it re-spawns itself as a detached
    child process.  In both cases the parent exits immediately and the child
    continues running the server in the background.

    When ``server-log-file`` is configured, standard error is redirected to
    that file instead of ``/dev/null`` so that all log output is captured.
    """
    from pathlib import Path

    log_path = papis.config.get("server-log-file")

    if hasattr(os, "fork"):
        # Unix
        if os.fork() > 0:
            sys.exit(0)

        os.setsid()  # type: ignore[attr-defined]  # To silence warnings on Windows

        if os.fork() > 0:
            sys.exit(0)

        sys.stdout.flush()
        sys.stderr.flush()

        devnull = os.open(os.devnull, os.O_RDWR)
        os.dup2(devnull, sys.stdin.fileno())

        if log_path:
            log_file = Path(log_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_fd = os.open(str(log_file), os.O_WRONLY | os.O_CREAT | os.O_APPEND)
            os.dup2(log_fd, sys.stdout.fileno())
            os.dup2(log_fd, sys.stderr.fileno())
            os.close(log_fd)
        else:
            os.dup2(devnull, sys.stdout.fileno())
            os.dup2(devnull, sys.stderr.fileno())

        os.close(devnull)
    else:
        # Windows
        args = [
            sys.executable,
            "-m",
            "papis",
            "server",
            "--port",
            str(port),
            "--host",
            host,
            "--_daemon",
        ]
        creationflags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP
            # NOTE: DETACHED_PROCESS is only defined on Windows; guard it so
            # mypy does not complain about a platform-conditional attribute.
            creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0)

        if log_path:
            log_file = Path(log_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(str(log_file), "a", encoding="utf-8") as target:
                subprocess.Popen(
                    args,
                    stdin=subprocess.DEVNULL,
                    stdout=target,
                    stderr=target,
                    creationflags=creationflags,
                )
        else:
            subprocess.Popen(
                args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
        sys.exit(0)


def _stop_server() -> None:
    """Stop a running background server.

    Sends ``SIGTERM`` to the process and waits for it to exit. If it does not exit,
    ``SIGKILL`` is sent.

    :raises SystemExit: If no PID file exists or the process is not running.
    """
    pid_file = _get_pid_file()
    if not pid_file.exists():
        logger.error("No server PID file found. Is the server running?")
        raise SystemExit(1)

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        logger.error("Invalid PID file at '%s'.", pid_file)
        pid_file.unlink(missing_ok=True)
        raise SystemExit(1) from None

    if not _pid_exists(pid):
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
        # The process exited between the liveness check above and the signal, so there
        # is nothing left to do.
        pid_file.unlink(missing_ok=True)
        logger.info("Server stopped.")
        return

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if not _pid_exists(pid):
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
            pass  # process already exited, so there's nothing to kill

    pid_file.unlink(missing_ok=True)
    logger.info("Server stopped.")


def _reject_if_already_running() -> None:
    """Refuse to start a second background server.

    :raises SystemExit: If another background server is already running.
    """
    pid_file = _get_pid_file()
    if not pid_file.exists():
        return

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        logger.warning("Removing invalid PID file at '%s'.", pid_file)
        pid_file.unlink(missing_ok=True)
        return

    if not _pid_exists(pid):
        logger.warning("Removing stale PID file (PID %s is not running).", pid)
        pid_file.unlink(missing_ok=True)
        return

    logger.error(
        "Server is already running (PID %s). Use 'papis server --stop' to stop it.",
        pid,
    )
    raise SystemExit(1) from None


@click.command("server")
@click.help_option("--help", "-h")
@click.option(
    "-p",
    "--port",
    help="Port to listen on.",
    type=int,
    default=lambda: papis.config.getint("server-port"),
)
@click.option(
    "--host",
    help="Host address to bind to.",
    type=str,
    default=lambda: papis.config.getstring("server-host"),
)
@papis.cli.bool_flag(
    "-b",
    "--background/--no-background",
    help="Run the server in the background.",
    default=lambda: papis.config.getboolean("server-background"),
)
@papis.cli.bool_flag(
    "--stop",
    help="Stop a running background server.",
    default=False,
)
@click.option(
    "--_daemon",
    help="Internal flag for Windows.",
    is_flag=True,
    hidden=True,
    default=False,
)
def cli(
    port: int,
    host: str,
    background: bool,
    stop: bool,
    _daemon: bool,
) -> None:
    """Start the Papis server."""
    if sys.platform == "win32" and (stop or background or _daemon):
        _ensure_psutil()

    if stop:
        _stop_server()
        return

    is_daemon = background or _daemon

    if is_daemon:
        _reject_if_already_running()

    if background and not _daemon:
        _daemonize(port, host)

    pid_file: Path | None = None
    if is_daemon:
        pid_file = _get_pid_file()
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()))

    log_level = os.environ.get("PAPIS_LOG_LEVEL", "INFO").lower()

    logger.info(
        "Starting Papis server on http://%s:%s (log level: %s).",
        host,
        port,
        log_level,
    )
    logger.info(
        "Interactive Swagger documentation available at http://%s:%s/docs.",
        host,
        port,
    )
    logger.info(
        "Redoc documentation available at http://%s:%s/redoc.",
        host,
        port,
    )
    if not is_daemon:
        logger.info("Press Ctrl+C to stop the server.")

    try:
        uvicorn.run(
            "papis.server.app:app",
            host=host,
            port=port,
            log_level=log_level,
        )
    finally:
        if pid_file is not None:
            pid_file.unlink(missing_ok=True)
