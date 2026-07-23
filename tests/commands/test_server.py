# ruff:file-ignore[import-private-name]

from __future__ import annotations

import os
import socket
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from papis.testing import PapisRunner, TemporaryConfiguration

# =============================================================================
# Helpers
# =============================================================================


def _free_port() -> int:
    """Bind an ephemeral socket to find a free TCP port for the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_for_server(port: int, timeout: float = 10.0) -> None:
    """Poll the server until it responds or *timeout* elapses.

    :raises AssertionError: if the server does not become ready in time, with
        the last connection error attached so the real failure is visible
        rather than a misleading cleanup error.
    """
    import time
    import urllib.request

    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/libraries")
            return
        except OSError as err:
            last_err = err
            time.sleep(0.1)

    raise AssertionError(
        f"server on port {port} did not start within {timeout}s: {last_err}"
    )


def _stop_background_server() -> None:
    """Best-effort cleanup: stop any running background server.

    No assertion is made here so that a failure during cleanup does not mask
    a more meaningful assertion error raised in the test body.
    """
    from papis.commands.server import cli

    runner = PapisRunner()
    runner.invoke(cli, ["--stop"])


def _start_background_server(port: int) -> None:
    """Start ``papis server --background`` and wait for the parent to exit."""
    import subprocess

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "papis",
            "server",
            "--port",
            str(port),
            "--background",
        ],
    )
    proc.wait(timeout=15 if sys.platform == "win32" else 3)
    assert proc.returncode == 0


# =============================================================================
# Tests
# =============================================================================


def test_pid_file_in_cache_home(tmp_config: TemporaryConfiguration) -> None:
    """The PID file is located inside the Papis cache directory."""
    from papis.commands.server import _get_pid_file
    from papis.utils import get_cache_home

    pid_file = _get_pid_file()
    assert str(pid_file.parent) == get_cache_home()


def test_stop_no_pid_file(
    tmp_config: TemporaryConfiguration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """``--stop`` fails cleanly when no server is running."""
    from papis.commands.server import cli

    runner = PapisRunner()
    result = runner.invoke(cli, ["--stop"])
    assert result.exit_code == 1
    assert "No server PID file found" in caplog.text


def test_stop_stale_pid_file(
    tmp_config: TemporaryConfiguration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """``--stop`` cleans up a stale PID file and exits successfully."""
    from papis.commands.server import _get_pid_file, cli

    # Create a PID file with a PID that is definitely not running
    pid_file = _get_pid_file()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(2**31 - 1))

    runner = PapisRunner()
    result = runner.invoke(cli, ["--stop"])
    assert result.exit_code == 0
    assert "not running" in caplog.text
    assert not _get_pid_file().exists()


def test_stop_invalid_pid_file(
    tmp_config: TemporaryConfiguration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """``--stop`` handles a corrupted PID file."""
    from papis.commands.server import _get_pid_file, cli

    _get_pid_file().write_text("not-a-number")

    runner = PapisRunner()
    result = runner.invoke(cli, ["--stop"])
    assert result.exit_code == 1
    assert "Invalid PID file" in caplog.text
    assert not _get_pid_file().exists()


def test_background_and_stop(tmp_config: TemporaryConfiguration) -> None:
    """Start the server in background, hit the API, stop it."""
    import urllib.request

    port = _free_port()

    try:
        _start_background_server(port)
        _wait_for_server(port)

        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/libraries")
        assert resp.status == 200
    finally:
        _stop_background_server()


def test_stop_kills_running_server(tmp_config: TemporaryConfiguration) -> None:
    """``--stop`` sends SIGTERM to a running background server."""
    port = _free_port()

    try:
        _start_background_server(port)
        _wait_for_server(port)

        # Read PID and verify the process is running
        from papis.commands.server import _get_pid_file, _pid_exists, cli

        pid_file = _get_pid_file()
        assert pid_file.exists()
        pid = int(pid_file.read_text().strip())
        assert _pid_exists(pid)

        # Stop it
        runner = PapisRunner()
        result = runner.invoke(cli, ["--stop"])
        assert result.exit_code == 0

        # Verify it's gone
        assert not _pid_exists(pid)
        assert not pid_file.exists()
    finally:
        _stop_background_server()


def test_log_file(tmp_config: TemporaryConfiguration) -> None:
    """``server-log-file`` redirects daemon output to the configured file."""
    import configparser
    import urllib.request

    log_path = os.path.join(tmp_config.tmpdir, "server.log")

    # Write ``server-log-file`` into the ``[settings]`` section of the config
    # file so that the background subprocess (a separate Python process) picks
    # it up; ``papis.config.set`` would only affect this process's in-memory
    # config.
    cfg = configparser.ConfigParser()
    cfg.read(tmp_config.configfile)
    cfg.set("settings", "server-log-file", log_path)
    with open(tmp_config.configfile, "w", encoding="utf-8") as fd:
        cfg.write(fd)

    port = _free_port()

    try:
        _start_background_server(port)
        _wait_for_server(port)

        # The server must be reachable (sanity) and the log file must exist
        # with server output in it.
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/libraries")
        assert resp.status == 200

        assert os.path.exists(log_path)
        with open(log_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        assert "Starting Papis server" in content
    finally:
        _stop_background_server()


def test_double_start_refused(tmp_config: TemporaryConfiguration) -> None:
    """A second background server is refused while one is already running."""
    import subprocess
    import urllib.request

    port1 = _free_port()
    port2 = _free_port()

    try:
        _start_background_server(port1)
        _wait_for_server(port1)

        # A second background server must be refused even on a different port,
        # since the PID file is shared regardless of host/port.
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "papis",
                "server",
                "--port",
                str(port2),
                "--background",
            ],
        )
        proc.wait(timeout=15 if sys.platform == "win32" else 3)
        assert proc.returncode == 1

        # The first server must still be running and reachable.
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port1}/api/v1/libraries")
        assert resp.status == 200
    finally:
        _stop_background_server()
