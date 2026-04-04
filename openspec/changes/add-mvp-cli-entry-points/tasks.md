## 1. CLI foundation

- [x] 1.1 Update `rust/Cargo.toml` with the MVP dependencies needed for clap, UUIDs, JSON handling, hashing, and tests, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.
- [x] 1.2 Replace the hello-world binary in `rust/src/main.rs` with clap-based entry points for `init`, `import-bib`, `add-pdf`, `list`, and `show`, add flat module stubs under `rust/src/`, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.

## 2. Library path and initialization

- [x] 2.1 Implement shared `--library` path resolution and validation logic so `init` can create a new library root while the other commands require an existing initialized library, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.
- [x] 2.2 Implement SQLite bootstrap code that creates `<library>/papis.sqlite3`, creates `<library>/storage/`, enables foreign keys, and makes `init` idempotent, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.

## 3. Schema and persistence

- [x] 3.1 Add the version-1 SQLite schema and lightweight migration path using `PRAGMA user_version`, including `entries`, `files`, and the required indexes, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.
- [x] 3.2 Add focused tests for reopening initialized libraries, preserving data across restarts, and surfacing unwritable or locked-library failures, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.

## 4. BibTeX import

- [x] 4.1 Implement the MVP entry and file models plus BibTeX-to-entry mapping for `bibtex_key`, `title`, nullable `year`, `authors_json`, `raw_bibtex`, and generated UUIDs, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.
- [x] 4.2 Implement `import-bib --library <path> <file.bib>` so it parses the whole file before writing, inserts valid non-duplicate entries, skips duplicate `bibtex_key` values, and fails cleanly on invalid BibTeX, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.

## 5. PDF attachment

- [x] 5.1 Implement entry lookup by `bibtex_key` plus PDF validation, SHA-256 hashing, and deterministic copy behavior to `storage/<entry_id>/main.pdf`, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.
- [x] 5.2 Implement `add-pdf --library <path> <bibtex_key> <file.pdf>` so it records `role`, `stored_relpath`, `source_path`, `sha256`, and `mime`, while rejecting missing or invalid PDFs without partial writes, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.

## 6. Read commands and end-to-end verification

- [x] 6.1 Implement `list --library <path>` and `show --library <path> <bibtex_key>` with stable SQLite-backed output for empty, populated, and not-found cases, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.
- [x] 6.2 Add end-to-end tests that initialize a temporary external library, import a `.bib`, attach a PDF, and then list and show the stored entry from a fresh process context, then run `cargo fmt`, `cargo clippy`, and `cargo test` in `rust/`.