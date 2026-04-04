## Why

The Rust rewrite needs a stable first slice that proves the project can manage a real library end to end without inheriting the Python implementation's complexity. The right place to start is the main CLI entry surface, because it fixes the MVP contract for where data lives, how users address entries, and which workflows must work before anything broader is added.

## What Changes

- Add the MVP command surface in the Rust binary with these subcommands: `init`, `import-bib`, `add-pdf`, `list`, and `show`.
- Define the MVP library contract so repo code remains under `rust/` and library data lives outside the repo through the required `--library <path>` argument.
- Add SQLite-backed persistence for entries and attached files using a minimal versioned schema and lightweight migrations.
- Import metadata from BibTeX `.bib` files into SQLite, including duplicate-key handling and invalid-input failures.
- Copy PDF files into library-managed storage and persist relative file paths in SQLite so the library remains portable.
- Keep the initial user-facing workflow intentionally small: initialize a library, import metadata, attach a PDF, then list and show entries.

## Non-goals

- No config-file discovery, interactive setup, or multi-library support for this MVP.
- No metadata fetchers, search, tags, notes, export, plugin system, or folder naming based on metadata.
- No changes under `python/`; the Python implementation remains reference-only while the MVP is built in `rust/`.

## Capabilities

### New Capabilities
- `mvp-library-cli`: A minimal single-user, single-library Rust CLI that initializes a library, imports BibTeX metadata, stores attached PDFs, and reads entry data back from SQLite.

### Modified Capabilities
- None.

## Impact

- Affected code is contained in `rust/`, starting from `main.rs` and simple supporting modules for CLI parsing, database access, BibTeX import, storage, and data models.
- The MVP depends on `clap` for command parsing, `rusqlite` for SQLite persistence, `serde` and `serde_json` for structured metadata, and `uuid` for stable internal entry identifiers.
- The stable CLI contract for this MVP is:
  - `papis-rs init --library <path>`
  - `papis-rs import-bib --library <path> <file.bib>`
  - `papis-rs add-pdf --library <path> <entry_ref> <file.pdf>`
  - `papis-rs list --library <path>`
  - `papis-rs show --library <path> <entry_ref>`
- Done for this change means a user can create a library, import a `.bib`, attach a PDF, and then successfully list and show that entry from the Rust CLI.