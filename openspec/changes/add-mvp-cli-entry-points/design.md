## Context

The Rust rewrite currently has an initialized crate but no MVP command surface, no library contract, and no SQLite-backed persistence. This change establishes the first end-to-end workflow for a single-user, single-library CLI while keeping all implementation work inside `rust/` and keeping library data outside the repo via the required `--library <path>` argument.

The technical design needs to stay beginner-friendly. That rules out a large framework, dynamic plugin behavior, and complex persistence layers. The MVP only needs enough structure to initialize a library, import BibTeX entries, attach one main PDF per entry, and read that data back through `list` and `show`.

## Goals / Non-Goals

**Goals:**
- Settle the Rust binary entry points around `init`, `import-bib`, `add-pdf`, `list`, and `show`.
- Define one library path resolution rule that every command uses consistently.
- Persist entries and file attachments in SQLite with a small schema and lightweight versioning.
- Keep the crate layout simple enough for a Rust beginner to navigate and extend.
- Support the MVP done path: initialize a library, import a `.bib`, attach a PDF, then list and show an entry.

**Non-Goals:**
- No plugin system, background services, or cross-process coordination beyond SQLite file locking.
- No config discovery, default library lookup, or interactive command flows.
- No search, tags, notes, export, remote metadata fetchers, or multi-file attachment workflows.
- No changes under `python/`; the Python tree is reference-only during this change.

## Decisions

### 1. The Rust binary SHALL expose the MVP commands directly from `main.rs`

`main.rs` will become the single clap entry point that defines or dispatches the five MVP subcommands. Supporting logic will live in flat modules under `rust/src/` such as `cli`, `db`, `bib`, `storage`, and `model`, but the public command surface is fixed in one place.

Why this choice:
- It settles the user-facing contract early.
- It keeps command discovery simple for a beginner.
- It matches the user's request to settle down the entry points in `main.rs`.

Alternative considered:
- Moving command definitions into many nested subcommand modules. This was rejected for MVP because it adds indirection before the behavior exists.

### 2. `--library` SHALL be required for every MVP command and resolved to a concrete filesystem path

The CLI will require `--library <path>` on `init`, `import-bib`, `add-pdf`, `list`, and `show`. Resolution rules are:
- Expand the provided path as given by the OS and convert it to an absolute path before use.
- `init` may create the target directory if it does not exist.
- All non-`init` commands require an existing library root containing `papis.sqlite3`.
- The library root must also contain `storage/`, which `init` ensures exists.
- Unwritable paths and SQLite-open failures are surfaced as command errors.

Why this choice:
- It preserves the required separation between repo code and user data.
- It avoids hidden state and config discovery in the MVP.

Alternative considered:
- A default library path in a config file. This was rejected because it violates the explicit `--library` contract in the MVP.

### 3. SQLite SHALL use a small hand-written migration path based on `PRAGMA user_version`

The database file lives at `<library>/papis.sqlite3`. On open, the application enables foreign keys and checks `PRAGMA user_version`. Version `0` means uninitialized; `init` creates the schema and sets `user_version = 1`. Re-running `init` against a version-1 database is idempotent.

Version 1 schema includes:
- `entries(entry_id TEXT PRIMARY KEY, bibtex_key TEXT UNIQUE NOT NULL, title TEXT, year INTEGER, authors_json TEXT NOT NULL, raw_bibtex TEXT NOT NULL, created_at TEXT NOT NULL)`
- `files(file_id TEXT PRIMARY KEY, entry_id TEXT NOT NULL REFERENCES entries(entry_id), role TEXT NOT NULL, stored_relpath TEXT NOT NULL, source_path TEXT NOT NULL, sha256 TEXT NOT NULL, mime TEXT NOT NULL)`
- An index on `files.entry_id`

Why this choice:
- It is enough to support persistence across restarts without introducing a migration framework.
- `user_version` is built into SQLite and easy to test.

Alternative considered:
- A dedicated Rust migration crate. This was rejected for MVP because it adds tooling and abstraction without reducing meaningful complexity at this stage.

### 4. Entry identity SHALL use an internal UUID and a user-facing `bibtex_key`

Each imported entry gets a generated UUID stored in `entry_id`. For the MVP CLI, `<entry_ref>` will mean `bibtex_key`, not UUID. `bibtex_key` is unique and human-readable, which makes the first manual workflow simpler.

The mapping is:
- `entry_id`: internal stable primary key used in the database and storage layout.
- `bibtex_key`: external reference accepted by `add-pdf` and `show` in the MVP.

Why this choice:
- It keeps storage paths stable even if display behavior changes later.
- It avoids forcing the user to copy UUIDs during the first usable workflow.

Alternative considered:
- Accepting both UUID and `bibtex_key` immediately. This was rejected for MVP because choosing one reference model keeps the command behavior simpler and the help text clearer.

### 5. BibTeX import SHALL be all-or-nothing for parse validity and skip duplicates by `bibtex_key`

The import flow reads the `.bib` file, parses all entries, converts the minimal fields needed by the schema, and only then starts database writes. If the BibTeX is invalid, the command fails without partial inserts. If an entry's `bibtex_key` already exists in the database, that entry is skipped and reported; other valid, non-duplicate entries in the same file may still be imported.

Why this choice:
- Invalid syntax should not leave the library in a partially imported state.
- Duplicate keys are an expected user-data issue and do not justify discarding unrelated valid entries.

Alternative considered:
- Failing the entire import on the first duplicate. This was rejected because duplicate-key handling is a normal maintenance case, not a structural parse failure.

### 6. PDF storage SHALL copy the source file to a deterministic relative path

`add-pdf` resolves the target entry by `bibtex_key`, creates `<library>/storage/<entry_id>/` if needed, and copies the source PDF to `<library>/storage/<entry_id>/main.pdf`. The application stores `stored_relpath` as the literal relative path `storage/<entry_id>/main.pdf`.

The file row also records:
- A generated `file_id`
- `role = "main"`
- The original `source_path` as provided or resolved by the OS
- The file `sha256`
- `mime`, expected to be `application/pdf` for accepted files

Why this choice:
- It is deterministic and portable.
- The path can be reconstructed or joined with the library root without depending on host-specific absolute paths.

Alternative considered:
- Organizing storage by title, year, or author. This was rejected because metadata-derived paths complicate renames, uniqueness, and debugging.

### 7. The crate layout SHALL stay flat and explicit

The MVP implementation will stay in a small set of modules under `rust/src/`:
- `main.rs` for clap wiring and top-level dispatch
- `cli.rs` for command handlers and output formatting
- `db.rs` for SQLite opening, migrations, and queries
- `bib.rs` for BibTeX parsing and mapping to entry models
- `storage.rs` for file validation, hashing, and copy logic
- `model.rs` for entry and file structs

Why this choice:
- It matches the preferred structure from the project context.
- It keeps responsibilities visible without introducing library-style complexity.

Alternative considered:
- A richer layered architecture with services, repositories, and traits. This was rejected because the MVP is too small to justify that extra structure.

## Risks / Trade-offs

- [BibTeX parsing library behavior may not expose raw entry text exactly as imported] -> Store the best available normalized raw BibTeX representation for MVP and document the limitation if exact block preservation is awkward.
- [Using only `bibtex_key` as the MVP entry reference may constrain future UX] -> Keep `entry_id` as the internal primary key so later commands can add UUID support without changing storage or schema.
- [SQLite file locking or unwritable library paths can produce platform-specific errors] -> Normalize these into explicit command failures and cover them in tests.
- [A flat module layout can become crowded later] -> Reorganize only after the MVP exists and real pressure points are visible.
- [Deterministic `main.pdf` storage overwrites prior main PDFs for the same entry] -> Treat one main PDF per entry as an intentional MVP constraint.

## Migration Plan

1. Create the clap-based command surface in `rust/src/main.rs` and supporting modules under `rust/src/`.
2. Add the SQLite bootstrap path that creates `<library>/papis.sqlite3`, `<library>/storage/`, and schema version 1.
3. Implement BibTeX import into the `entries` table with duplicate-key reporting.
4. Implement PDF attachment into the `files` table with deterministic copy behavior.
5. Implement `list` and `show` against SQLite so the full done path can be executed from a fresh library.
6. Verify with `cargo fmt`, `cargo clippy`, and `cargo test` after each implementation chunk.

Rollback is local and simple during MVP development: discard the generated library directory used for testing and remove unmerged Rust code changes. No data migration for existing users is needed because this feature set does not yet exist in the Rust binary.

## Open Questions

- Whether the chosen BibTeX crate exposes enough structured author data for a clean `authors_json` representation without extra normalization code.
- Whether MIME validation should rely on a simple PDF signature check or a dedicated MIME-detection crate during MVP implementation.