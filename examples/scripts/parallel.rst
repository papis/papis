Preview public CS references with Parallel
=========================================

``papis-parallel.py`` is an optional example for finding public software
engineering documentation and computer science references. It calls the
``web_search`` tool on Parallel's Unified MCP server, then saves titles and
original source URLs for Papis's existing JSON explorer. It is not installed
with Papis.

Install the optional MCP client in the Python environment used for the script::

    python -m pip install 'mcp>=1.26,<2'

See `Parallel MCP setup
<https://docs.parallel.ai/integrations/mcp/quickstart>`__ for service details.
This example uses ``https://mcp.parallel.ai/mcp`` without a key, with the
``papis-parallel-example/0.1`` User-Agent. Keyless access is rate limited.
The example was contributed by Parallel DevRel.

Search, preview, and select
---------------------------

From the repository root, explicitly send a public documentation query::

    python examples/scripts/papis-parallel.py search \
        --public-query 'site:docs.python.org asyncio TaskGroup documentation' \
        --out references.json

Only ``search`` contacts Parallel. The query is sent to that service; use public
keywords only, never private documents, code, or library contents. Search results
are candidates for your review, not verified bibliographic metadata. The script
prints numbered titles and URLs (escaped for terminal display) and saves their
exact strings in JSON. Missing titles, malformed responses, and non-HTTP(S) URLs
are rejected. An empty search saves an empty list and reports no references.

Review the saved results and explicitly select one by its displayed number::

    python examples/scripts/papis-parallel.py preview references.json
    python examples/scripts/papis-parallel.py select references.json \
        --number 1 --out selected.json

These two commands work offline. Output files must be new paths. Selection uses
the saved list, so changing search rankings cannot change the selected reference.
Only ``title`` and ``url`` are retained; no DOI, author, date, excerpts, or file
downloads are inferred. If you have an independently known DOI, use Papis's
existing ``papis add --from doi DOI`` provider to verify it separately.

Try native ingestion in a disposable library
--------------------------------------------

The script does not import anything itself. In a POSIX shell, use a temporary
configuration, cache, and empty library to try Papis's normal ingestion::

    demo_dir=$(mktemp -d)
    mkdir -p "$demo_dir/config" "$demo_dir/cache" "$demo_dir/library"
    printf '[settings]\ndefault-library = demo\n\n[demo]\ndir = %s\n' \
        "$demo_dir/library" > "$demo_dir/config/config"
    export PAPIS_CONFIG_DIR="$demo_dir/config"
    export PAPIS_CACHE_DIR="$demo_dir/cache"
    export PAPIS_LIB=demo
    papis explore json selected.json add
    papis list --all --format '{doc[title]} | {doc[url]}'

The selected title and source URL become a metadata-only Papis entry, ready for
``papis browse``. No source page or PDF is downloaded. Run the example in a fresh
shell and close it afterward to discard the temporary environment settings.
The demo directory can be removed when you have finished inspecting it.
