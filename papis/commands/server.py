"""
The ``server`` command starts the Papis API server.

The server exposes a JSON REST API for managing libraries.

Examples
^^^^^^^^

- Start the server on the default URL:

    .. code:: sh

        papis server

- Start the server bound to all interfaces on a custom port:

    .. code:: sh

        papis server --server-url http://0.0.0.0:9000

- Start the server in the background:

    .. code:: sh

        papis server --background

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.server:cli
    :prog: papis server
"""

from __future__ import annotations

import sys

import click

import papis.cli
import papis.config
from papis.server.runtime import (
    get_pid_file,
    pid_exists,
    serve,
    stop_server,
)


def _show_status() -> None:
    """Print server status: running state, mode, and transport details."""
    pid_file = get_pid_file()

    if not pid_file.exists():
        click.echo("Server is not running.")
        return

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        click.echo(f"Cannot read PID file: {pid_file}.")
        return

    if not pid_exists(pid):
        click.echo(f"Server is not running (stale PID file for PID {pid}).")
        return

    click.echo("Server is running")
    click.echo(f"  PID: {pid}")

    url = papis.config.get("server-url")
    local = papis.config.getboolean("server-local-mode")
    click.echo(f"  Mode: {'local' if local else 'remote'}")
    click.echo(f"  Address: {url}")


@click.command("server")
@click.help_option("--help", "-h")
@click.option(
    "-u",
    "--server-url",
    help="URL to listen on (e.g. http://127.0.0.1:8383).",
    type=str,
    default=lambda: papis.config.get("server-url"),
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
@papis.cli.bool_flag(
    "--status",
    help="Show server status (running state, mode, transport details).",
    default=False,
)
def cli(
    server_url: str,
    background: bool,
    stop: bool,
    status: bool,
) -> None:
    """Start the Papis server."""
    if status:
        _show_status()
        return

    if stop:
        stop_server()
        return

    serve(server_url, background=background)

    if background:
        sys.exit(0)
