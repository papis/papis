#! /usr/bin/env python3
# papis-short-help: Preview public CS references with Parallel.
"""Search public software documentation and CS references, then select metadata.

See ``parallel.rst`` in this directory for setup and a disposable-library example.
Only ``search`` contacts Parallel. This script never writes to a Papis library.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Sequence

SERVER_URL = "https://mcp.parallel.ai/mcp"
USER_AGENT = "papis-parallel-example/0.1"
TIMEOUT = 45


def references(data: object) -> list[dict[str, str]]:
    """Validate references and retain exact titles and URLs, without other fields."""
    if not isinstance(data, list):
        raise ValueError("Expected a list of references.")

    docs = []
    for number, item in enumerate(data, 1):
        if not isinstance(item, dict):
            raise ValueError(f"Reference {number} must be an object.")
        title, url = item.get("title"), item.get("url")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"Reference {number} needs a title.")
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"Reference {number} needs a URL.")
        parts = urlsplit(url)
        if (parts.scheme not in {"http", "https"} or not parts.hostname
                or parts.username is not None or parts.password is not None
                or any(c.isspace() or ord(c) < 32 for c in url)):
            raise ValueError(f"Reference {number} needs an HTTP(S) source URL.")
        docs.append({"title": title, "url": url})
    return docs


def search_result(result: object) -> list[dict[str, str]]:
    """Read an MCP tool result, preferring its structured JSON response."""
    if not isinstance(result, dict) or result.get("isError"):
        raise ValueError("Parallel web_search returned an error.")
    data = result.get("structuredContent")
    if data is None:
        blocks = result.get("content")
        if not isinstance(blocks, list) or len(blocks) != 1:
            raise ValueError("Expected one JSON text result from web_search.")
        block = blocks[0]
        if (not isinstance(block, dict) or block.get("type") != "text"
                or not isinstance(block.get("text"), str)):
            raise ValueError("Expected a JSON text result from web_search.")
        data = json.loads(block["text"])
    if not isinstance(data, dict) or "results" not in data:
        raise ValueError("Parallel web_search response has no results list.")
    return references(data["results"])


async def search(query: str) -> object:
    """Call only web_search, with a public query and no account credentials."""
    # Optional example dependencies are not installed by Papis or its CI extras.
    import httpx  # ty: ignore[import-not-found]
    from mcp import ClientSession  # ty: ignore[import-not-found]
    from mcp.client.streamable_http import streamable_http_client  # ty: ignore[import-not-found]
    from mcp.types import Implementation  # ty: ignore[import-not-found]

    async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT) as client:
        async with streamable_http_client(
                SERVER_URL, http_client=client) as (read, write, _):
            async with ClientSession(
                    read, write,
                    read_timeout_seconds=timedelta(seconds=TIMEOUT),
                    client_info=Implementation(
                        name="papis-parallel-example", version="0.1")) as session:
                await session.initialize()
                result = await session.call_tool("web_search", {
                    "objective": "Find public software engineering documentation "
                                 "or computer science references for a reading list. "
                                 "Return original page titles and source URLs.",
                    "search_queries": [query],
                })
                return result.model_dump(by_alias=True)


def preview(docs: list[dict[str, str]]) -> None:
    """Print stable selection numbers and escaped metadata for terminal display."""
    if not docs:
        print("No references found.")
    for number, doc in enumerate(docs, 1):
        print(f"{number}. {json.dumps(doc['title'], ensure_ascii=True)}")
        print(f"   {json.dumps(doc['url'], ensure_ascii=True)}")


def save(path: Path, docs: list[dict[str, str]]) -> None:
    """Write an explorer JSON file without replacing an existing file."""
    with path.open("x", encoding="utf-8") as stream:
        json.dump(docs, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    search_parser = commands.add_parser(
        "search", help="Send a public CS/documentation query to Parallel.")
    search_parser.add_argument(
        "--public-query", required=True,
        help="Public keywords only (sent to Parallel); never include private text.")
    search_parser.add_argument("--out", required=True, type=Path)
    preview_parser = commands.add_parser("preview", help="Preview a saved JSON file.")
    preview_parser.add_argument("file", type=Path)
    select_parser = commands.add_parser("select", help="Select one saved reference.")
    select_parser.add_argument("file", type=Path)
    select_parser.add_argument("--number", required=True, type=int)
    select_parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        if args.command == "search":
            if not args.public_query.strip():
                parser.error("--public-query must not be empty")
            if args.out.exists():
                parser.error("--out already exists; choose a new file")
            try:
                result = asyncio.run(asyncio.wait_for(
                    search(args.public_query), timeout=TIMEOUT))
            except ImportError:
                parser.exit(1, "Search needs the optional 'mcp>=1.26,<2' package.\n")
            except Exception:
                parser.exit(1, "Parallel search failed; check connectivity and "
                            "keyless rate limits. No output written.\n")
            docs = search_result(result)
        else:
            docs = references(json.loads(args.file.read_text(encoding="utf-8")))
            if args.command == "select":
                if not 1 <= args.number <= len(docs):
                    parser.error("--number must be one of the previewed numbers")
                docs = [docs[args.number - 1]]
        preview(docs)
        if args.command != "preview":
            save(args.out, docs)
            print(f"Saved {len(docs)} reference(s) to {args.out}.", file=sys.stderr)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
