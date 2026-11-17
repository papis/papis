from __future__ import annotations

import asyncio
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from papis.testing import TemporaryLibrary

SCRIPT = Path(__file__).parents[1] / "examples" / "scripts" / "papis-parallel.py"
DOCS = [
    {"title": "Task groups — Python",
     "url": "https://docs.python.org/3/library/asyncio-task.html#task-groups"},
    {"title": "  Structured concurrency  ",
     "url": "https://example.org/cs?q=a%20b&n=2#reading"},
]


@pytest.fixture
def example() -> Any:
    spec = importlib.util.spec_from_file_location("parallel_example", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_metadata_and_mcp_envelopes(example: Any) -> None:
    raw = [{**doc, "doi": "unverified", "files": ["/private/file"]} for doc in DOCS]
    assert example.references(raw) == DOCS
    for envelope in [
        {"structuredContent": {"results": raw}, "content": []},
        {"content": [{"type": "text", "text": json.dumps({"results": raw})}]},
    ]:
        assert example.search_result(envelope) == DOCS
    assert example.search_result({"structuredContent": {"results": []}}) == []


@pytest.mark.parametrize("data", [
    {}, [None], [{"title": "", "url": "https://example.org"}],
    [{"title": "Title", "url": None}],
    [{"title": "Title", "url": "file:///tmp/document"}],
    [{"title": "Title", "url": "https://user:password@example.org"}],
    [{"title": "Title", "url": "https://example.org/\npage"}],
    [{"title": "Title", "url": "https://[invalid"}],
])
def test_malformed_references(example: Any, data: object) -> None:
    with pytest.raises(ValueError):
        example.references(data)


@pytest.mark.parametrize("result", [
    {"isError": True, "structuredContent": {"results": DOCS}},
    {"structuredContent": {}}, {"structuredContent": {"results": None}},
    {"content": []}, {"content": [{"type": "image"}]},
    {"content": [{"type": "text", "text": "not JSON"}]},
])
def test_malformed_mcp_results(example: Any, result: object) -> None:
    with pytest.raises(ValueError):
        example.search_result(result)


def test_offline_preview_and_explicit_selection(
        example: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source, selected = tmp_path / "results.json", tmp_path / "selected.json"
    source.write_text(json.dumps(DOCS), encoding="utf-8")
    assert example.main(["preview", str(source)]) == 0
    assert "1. " in capsys.readouterr().out
    for number in ("0", "-1", "3"):
        with pytest.raises(SystemExit) as exc:
            example.main(["select", str(source), "--number", number,
                          "--out", str(selected)])
        assert exc.value.code == 2
        assert not selected.exists()
    with pytest.raises(SystemExit):
        example.main(["select", str(source), "--out", str(selected)])
    assert example.main(["select", str(source), "--number", "2",
                         "--out", str(selected)]) == 0
    assert json.loads(selected.read_text()) == [DOCS[1]]
    with pytest.raises(SystemExit):
        example.main(["select", str(source), "--number", "1",
                      "--out", str(selected)])
    assert json.loads(selected.read_text()) == [DOCS[1]]


def test_preview_escapes_terminal_controls(
        example: Any, capsys: pytest.CaptureFixture[str]) -> None:
    example.preview([{"title": "Escape \x1b[2J", "url": DOCS[0]["url"]}])
    output = capsys.readouterr().out
    assert "\x1b" not in output
    assert "\\u001b" in output


def test_help_without_optional_dependencies() -> None:
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(SCRIPT), "--help"],
        capture_output=True, text=True, check=True)
    assert "search" in result.stdout and "select" in result.stdout


@pytest.mark.parametrize("failure", [None, "tool", "unavailable", "timeout", "empty"])
def test_search_transport(
        example: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        failure: str | None) -> None:
    # Use the real MCP client with a supported HTTPX transport double. No network.
    pytest.importorskip("mcp")
    import httpx  # ty: ignore[import-not-found]

    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["User-Agent"] == example.USER_AGENT
        assert "authorization" not in request.headers
        assert "x-api-key" not in request.headers
        assert str(request.url) == example.SERVER_URL
        if failure == "unavailable":
            return httpx.Response(503)
        if failure == "timeout":
            raise httpx.ReadTimeout("Test timeout", request=request)
        if request.method == "GET":
            return httpx.Response(405)
        if request.method == "DELETE":
            return httpx.Response(200)
        data = json.loads(request.content)
        method = data["method"]
        if "id" not in data:
            return httpx.Response(202)
        if method == "initialize":
            result = {"protocolVersion": "2025-11-25", "capabilities": {},
                      "serverInfo": {"name": "fixture", "version": "1"}}
        elif method == "tools/list":
            result = {"tools": [{"name": "web_search", "inputSchema": {
                "type": "object", "properties": {}}}]}
        else:
            assert method == "tools/call"
            assert data["params"]["name"] == "web_search"
            arguments = data["params"]["arguments"]
            assert arguments["search_queries"] == ["asyncio TaskGroup documentation"]
            assert set(arguments) == {"objective", "search_queries"}
            result = {
                "isError": failure == "tool",
                "content": [{"type": "text", "text": json.dumps({
                    "results": [] if failure == "empty" else DOCS})}],
            }
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": data["id"],
                                         "result": result})

    client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: client(
        transport=httpx.MockTransport(handler), **kwargs))
    # Ambient Parallel credentials are deliberately ignored by this keyless example.
    monkeypatch.setenv("PARALLEL_API_KEY", "unused-test-value")
    output = tmp_path / "results.json"
    args = ["search", "--public-query", "asyncio TaskGroup documentation",
            "--out", str(output)]
    if failure in {"tool", "unavailable", "timeout"}:
        with pytest.raises(SystemExit) as exc:
            example.main(args)
        assert exc.value.code == 1
        assert not output.exists()
    else:
        assert example.main(args) == 0
        assert json.loads(output.read_text()) == ([] if failure == "empty" else DOCS)
    assert requests
    if failure not in {"unavailable", "timeout"}:
        calls = [json.loads(r.content) for r in requests if r.method == "POST"]
        assert sum(c["method"] == "tools/call" for c in calls) == 1


def test_search_requires_public_query(
        example: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async def unexpected(query: str) -> None:
        await asyncio.sleep(0)
        pytest.fail("No request expected")

    monkeypatch.setattr(example, "search", unexpected)
    output = tmp_path / "results.json"
    for args in (["search", "--out", str(output)],
                 ["search", "--public-query", "  ", "--out", str(output)]):
        with pytest.raises(SystemExit) as exc:
            example.main(args)
        assert exc.value.code == 2
        assert not output.exists()


def test_total_deadline(
        example: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async def slow(query: str) -> None:
        await asyncio.sleep(1)

    monkeypatch.setattr(example, "search", slow)
    monkeypatch.setattr(example, "TIMEOUT", 0.01)
    output = tmp_path / "results.json"
    with pytest.raises(SystemExit) as exc:
        example.main(["search", "--public-query", "public CS reference",
                      "--out", str(output)])
    assert exc.value.code == 1
    assert not output.exists()


@pytest.mark.library_setup(populate=False)
def test_native_explorer_ingestion(
        example: Any, tmp_library: TemporaryLibrary, tmp_path: Path) -> None:
    from papis.commands.default import run
    from papis.testing import PapisRunner

    source, selected = tmp_path / "results.json", tmp_path / "selected.json"
    source.write_text(json.dumps(DOCS), encoding="utf-8")
    assert not list(Path(tmp_library.libdir).glob("*/info.yaml"))
    assert example.main(["preview", str(source)]) == 0
    assert not list(Path(tmp_library.libdir).glob("*/info.yaml"))
    assert example.main(["select", str(source), "--number", "2",
                         "--out", str(selected)]) == 0
    runner = PapisRunner()
    result = runner.invoke(run, ["explore", "json", str(selected), "add"])
    assert result.exit_code == 0

    from papis.yaml import yaml_to_data

    info, = Path(tmp_library.libdir).glob("*/info.yaml")
    imported = yaml_to_data(str(info))
    assert {key: imported[key] for key in ("title", "url")} == DOCS[1]
    assert "doi" not in imported
    assert len(list(info.parent.iterdir())) == 1
    listed = runner.invoke(run, ["list", "--all", "--format", "{doc[url]}"])
    assert listed.exit_code == 0 and DOCS[1]["url"] in listed.output
    explorers = runner.invoke(run, ["list", "--explorers"])
    assert explorers.exit_code == 0
    assert "crossref" in explorers.output and "json" in explorers.output
    assert "parallel" not in explorers.output
