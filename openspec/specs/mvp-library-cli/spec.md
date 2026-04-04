## ADDED Requirements

### Requirement: The CLI SHALL initialize and reopen an MVP library
The system SHALL provide `papis-rs init --library <path>` to create or validate a single-user library whose runtime data lives outside the repo. A valid initialized library SHALL contain `<library>/papis.sqlite3` and `<library>/storage/`. Re-running `init` against an existing initialized library SHALL succeed without duplicating schema objects or corrupting existing data.

#### Scenario: Initialize a new library
- **WHEN** the user runs `papis-rs init --library <path>` for a path that does not yet contain a library
- **THEN** the system creates the library root as needed, creates `papis.sqlite3`, creates `storage/`, initializes schema version 1, and exits successfully

#### Scenario: Re-run init on an existing library
- **WHEN** the user runs `papis-rs init --library <path>` for a library that already contains schema version 1 and existing entry data
- **THEN** the system exits successfully without deleting data, duplicating tables, or changing existing rows

#### Scenario: Use a library after restart
- **WHEN** the user initializes a library, exits the process, and later runs another MVP command with the same `--library <path>`
- **THEN** the system reopens the same SQLite database and the previously stored data remains available

#### Scenario: Reject an unwritable library path
- **WHEN** the user runs an MVP command with a `--library <path>` that cannot be created or opened for writing
- **THEN** the system fails the command with a clear error and does not report success

#### Scenario: Report a locked SQLite database
- **WHEN** the user runs an MVP command and the SQLite database cannot be written because it is locked
- **THEN** the system fails the command with a clear database-access error and does not perform a partial write

### Requirement: The CLI SHALL import BibTeX metadata into SQLite
The system SHALL provide `papis-rs import-bib --library <path> <file.bib>` to parse one BibTeX file containing one or more entries and store the imported metadata in SQLite. Each stored entry SHALL receive a generated UUID `entry_id`, a unique `bibtex_key`, and the minimal MVP metadata needed by the schema, including `title`, nullable `year`, `authors_json`, `raw_bibtex`, and `created_at`.

#### Scenario: Import multiple BibTeX entries
- **WHEN** the user runs `papis-rs import-bib --library <path> <file.bib>` on a valid file containing multiple BibTeX entries with distinct keys
- **THEN** the system stores each entry in SQLite and makes them available to `list` and `show`

#### Scenario: Reject invalid BibTeX input
- **WHEN** the user runs `papis-rs import-bib --library <path> <file.bib>` on a file with invalid BibTeX syntax
- **THEN** the system fails the command, reports that the BibTeX input is invalid, and does not insert any rows from that command

#### Scenario: Skip duplicate BibTeX keys already in the library
- **WHEN** the user imports a BibTeX file that contains an entry whose `bibtex_key` already exists in the library
- **THEN** the system skips that duplicate entry, preserves the existing row, imports any other valid non-duplicate entries, and reports that duplicates were skipped

#### Scenario: Skip duplicate BibTeX keys within the same file
- **WHEN** the user imports a BibTeX file that repeats the same `bibtex_key` more than once
- **THEN** the system imports at most one row for that key, skips the duplicate occurrences, and reports that duplicates were skipped

### Requirement: The CLI SHALL copy and record one main PDF per entry
The system SHALL provide `papis-rs add-pdf --library <path> <entry_ref> <file.pdf>` to attach one main PDF to an existing entry. For the MVP, `<entry_ref>` SHALL be the entry's `bibtex_key`. On success, the system SHALL copy the source file to `<library>/storage/<entry_id>/main.pdf` and store a row in `files` with a portable `stored_relpath` relative to the library root.

#### Scenario: Attach a valid PDF to an existing entry
- **WHEN** the user runs `papis-rs add-pdf --library <path> <bibtex_key> <file.pdf>` for an existing entry and a valid PDF source file
- **THEN** the system copies the file to `storage/<entry_id>/main.pdf`, stores that relative path in SQLite, records the source path, sha256, and MIME value, and exits successfully

#### Scenario: Reject a missing PDF path
- **WHEN** the user runs `papis-rs add-pdf --library <path> <bibtex_key> <file.pdf>` and the source file does not exist
- **THEN** the system fails the command with a clear file-not-found error and does not insert a `files` row

#### Scenario: Reject a non-PDF input
- **WHEN** the user runs `papis-rs add-pdf --library <path> <bibtex_key> <file.pdf>` and the provided file is not a valid PDF
- **THEN** the system fails the command with a clear invalid-file-type error and does not insert a `files` row

### Requirement: The CLI SHALL list imported entries from SQLite
The system SHALL provide `papis-rs list --library <path>` to read entries from SQLite and show a stable summary of the imported library contents.

#### Scenario: List entries after import
- **WHEN** the user runs `papis-rs list --library <path>` after importing one or more entries
- **THEN** the system displays each stored entry from SQLite with enough information to identify it, including its `bibtex_key`

#### Scenario: List an empty library
- **WHEN** the user runs `papis-rs list --library <path>` for an initialized library with no entries
- **THEN** the system exits successfully and reports that no entries are stored

### Requirement: The CLI SHALL show one entry and its attached files from SQLite
The system SHALL provide `papis-rs show --library <path> <entry_ref>` to display the stored metadata for one entry and its attached files. For the MVP, `<entry_ref>` SHALL be the entry's `bibtex_key`.

#### Scenario: Show an imported entry with an attached PDF
- **WHEN** the user runs `papis-rs show --library <path> <bibtex_key>` for an entry that has been imported and has a main PDF attached
- **THEN** the system displays the stored entry metadata and the recorded attached-file information, including the relative stored path

#### Scenario: Show an imported entry without attached files
- **WHEN** the user runs `papis-rs show --library <path> <bibtex_key>` for an entry that exists but has no files
- **THEN** the system displays the entry metadata and indicates that no attached files are recorded

#### Scenario: Reject an unknown entry reference
- **WHEN** the user runs `papis-rs show --library <path> <bibtex_key>` for a key that does not exist in the library
- **THEN** the system fails the command with a clear not-found error