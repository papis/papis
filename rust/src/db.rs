//! SQLite database access: opening connections, running migrations,
//! and executing queries against the library's `papis.sqlite3` file.
//!
//! The database file lives at `<library>/papis.sqlite3`.  On first open
//! (`init`), the module creates the schema and sets `PRAGMA user_version = 1`.
//! Subsequent opens check that `user_version` matches an expected version.

use std::path::Path;

use rusqlite::Connection;

/// Well-known database filename inside every library root.
pub const DB_FILENAME: &str = "papis.sqlite3";

/// The latest schema version, tracked via `PRAGMA user_version`.
const SCHEMA_VERSION: u32 = 1;

// ---------------------------------------------------------------------------
// Version-1 DDL (entries, files, index)
// ---------------------------------------------------------------------------

/// SQL statements that create the version-1 schema.
///
/// - `entries` stores imported BibTeX metadata.  `entry_id` is a UUID primary
///   key; `bibtex_key` is the unique human-facing reference.
/// - `files` stores attached-file metadata.  `entry_id` is a foreign key that
///   points back to `entries`.
/// - An index on `files.entry_id` speeds up the join used by `show`.
const SCHEMA_V1: &str = "
CREATE TABLE IF NOT EXISTS entries (
    entry_id    TEXT PRIMARY KEY,
    bibtex_key  TEXT UNIQUE NOT NULL,
    title       TEXT,
    year        INTEGER,
    authors_json TEXT NOT NULL,
    raw_bibtex  TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    file_id        TEXT PRIMARY KEY,
    entry_id       TEXT NOT NULL REFERENCES entries(entry_id),
    role           TEXT NOT NULL,
    stored_relpath TEXT NOT NULL,
    source_path    TEXT NOT NULL,
    sha256         TEXT NOT NULL,
    mime           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_files_entry_id ON files(entry_id);
";

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/// Open (or create) the SQLite database and ensure foreign keys are enabled.
///
/// This is the single entry point for obtaining a database connection.
/// It does **not** run migrations – call [`initialize_schema`] for that.
pub fn open_db(library: &Path) -> anyhow::Result<Connection> {
    let db_path = library.join(DB_FILENAME);
    let conn = Connection::open(&db_path)
        .map_err(|e| anyhow::anyhow!("Failed to open database at {}: {}", db_path.display(), e))?;

    // Foreign-key enforcement is off by default in SQLite; turn it on for
    // every connection so that `files.entry_id` references are validated.
    conn.execute_batch("PRAGMA foreign_keys = ON;")?;

    Ok(conn)
}

/// Create the version-1 schema if the database is uninitialized.
///
/// "Uninitialized" means `user_version == 0`.  If the DB is already at
/// version 1 the call is a no-op (idempotent).  Any other version is
/// rejected because we only know how to handle version 0 → 1 right now.
pub fn initialize_schema(conn: &Connection) -> anyhow::Result<()> {
    let version: u32 = conn.pragma_query_value(None, "user_version", |row| row.get(0))?;

    match version {
        0 => {
            // Fresh database – create tables and bump the version.
            conn.execute_batch(SCHEMA_V1)?;
            conn.pragma_update(None, "user_version", SCHEMA_VERSION)?;
            Ok(())
        }
        v if v == SCHEMA_VERSION => {
            // Already at the expected version – nothing to do.
            Ok(())
        }
        other => {
            anyhow::bail!(
                "Unsupported database schema version {other} (expected {SCHEMA_VERSION})"
            );
        }
    }
}

/// Return the current `user_version` of the database.
///
/// Useful for tests that want to assert the schema was applied.
pub fn schema_version(conn: &Connection) -> anyhow::Result<u32> {
    let v: u32 = conn.pragma_query_value(None, "user_version", |row| row.get(0))?;
    Ok(v)
}

// ---------------------------------------------------------------------------
// Entry insertion
// ---------------------------------------------------------------------------

use crate::model::Entry;

/// Insert result describing what happened for a batch of entries.
pub struct InsertResult {
    /// Number of entries successfully inserted.
    pub inserted: usize,
    /// BibTeX keys that were skipped because they already exist in the DB.
    pub skipped_keys: Vec<String>,
}

/// Insert a batch of entries into the database, skipping any whose
/// `bibtex_key` already exists.
///
/// Uses `INSERT OR IGNORE` so that the UNIQUE constraint on `bibtex_key`
/// silently skips duplicates without aborting the transaction.  The caller
/// receives a count of how many rows were actually inserted and a list of
/// the keys that were skipped.
pub fn insert_entries(conn: &Connection, entries: &[Entry]) -> anyhow::Result<InsertResult> {
    let mut inserted = 0usize;
    let mut skipped_keys = Vec::new();

    let tx = conn.unchecked_transaction()?;

    for entry in entries {
        let changes = tx.execute(
            "INSERT OR IGNORE INTO entries
                (entry_id, bibtex_key, title, year, authors_json, raw_bibtex, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            rusqlite::params![
                entry.entry_id,
                entry.bibtex_key,
                entry.title,
                entry.year,
                entry.authors_json,
                entry.raw_bibtex,
                entry.created_at,
            ],
        )?;

        if changes == 0 {
            // The UNIQUE constraint on bibtex_key caused the row to be
            // silently ignored – record it as skipped.
            skipped_keys.push(entry.bibtex_key.clone());
        } else {
            inserted += 1;
        }
    }

    tx.commit()?;
    Ok(InsertResult {
        inserted,
        skipped_keys,
    })
}

// ---------------------------------------------------------------------------
// Entry retrieval
// ---------------------------------------------------------------------------

use crate::model::FileRecord;

/// Retrieve all entries ordered by `bibtex_key`.
pub fn list_entries(conn: &Connection) -> anyhow::Result<Vec<Entry>> {
    let mut stmt = conn.prepare(
        "SELECT entry_id, bibtex_key, title, year, authors_json, raw_bibtex, created_at
         FROM entries ORDER BY bibtex_key",
    )?;
    let rows = stmt.query_map([], |row| {
        Ok(Entry {
            entry_id: row.get(0)?,
            bibtex_key: row.get(1)?,
            title: row.get(2)?,
            year: row.get(3)?,
            authors_json: row.get(4)?,
            raw_bibtex: row.get(5)?,
            created_at: row.get(6)?,
        })
    })?;
    let mut entries = Vec::new();
    for row in rows {
        entries.push(row?);
    }
    Ok(entries)
}

/// Look up a single entry by its `bibtex_key`.
/// Returns `None` if no entry has that key.
pub fn find_entry_by_key(conn: &Connection, bibtex_key: &str) -> anyhow::Result<Option<Entry>> {
    let mut stmt = conn.prepare(
        "SELECT entry_id, bibtex_key, title, year, authors_json, raw_bibtex, created_at
         FROM entries WHERE bibtex_key = ?1",
    )?;
    let mut rows = stmt.query_map([bibtex_key], |row| {
        Ok(Entry {
            entry_id: row.get(0)?,
            bibtex_key: row.get(1)?,
            title: row.get(2)?,
            year: row.get(3)?,
            authors_json: row.get(4)?,
            raw_bibtex: row.get(5)?,
            created_at: row.get(6)?,
        })
    })?;
    match rows.next() {
        Some(row) => Ok(Some(row?)),
        None => Ok(None),
    }
}

/// Retrieve all file records for a given `entry_id`.
pub fn files_for_entry(conn: &Connection, entry_id: &str) -> anyhow::Result<Vec<FileRecord>> {
    let mut stmt = conn.prepare(
        "SELECT file_id, entry_id, role, stored_relpath, source_path, sha256, mime
         FROM files WHERE entry_id = ?1",
    )?;
    let rows = stmt.query_map([entry_id], |row| {
        Ok(FileRecord {
            file_id: row.get(0)?,
            entry_id: row.get(1)?,
            role: row.get(2)?,
            stored_relpath: row.get(3)?,
            source_path: row.get(4)?,
            sha256: row.get(5)?,
            mime: row.get(6)?,
        })
    })?;
    let mut files = Vec::new();
    for row in rows {
        files.push(row?);
    }
    Ok(files)
}

/// Insert a single file record into the `files` table.
pub fn insert_file(conn: &Connection, file: &FileRecord) -> anyhow::Result<()> {
    conn.execute(
        "INSERT INTO files (file_id, entry_id, role, stored_relpath, source_path, sha256, mime)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        rusqlite::params![
            file.file_id,
            file.entry_id,
            file.role,
            file.stored_relpath,
            file.source_path,
            file.sha256,
            file.mime,
        ],
    )?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    /// Helper: create a temp library dir and open a fresh DB inside it.
    fn tmp_db() -> (TempDir, Connection) {
        let tmp = TempDir::new().unwrap();
        let conn = open_db(tmp.path()).unwrap();
        (tmp, conn)
    }

    #[test]
    fn fresh_db_has_version_zero() {
        let (_tmp, conn) = tmp_db();
        assert_eq!(schema_version(&conn).unwrap(), 0);
    }

    #[test]
    fn initialize_schema_sets_version_one() {
        let (_tmp, conn) = tmp_db();
        initialize_schema(&conn).unwrap();
        assert_eq!(schema_version(&conn).unwrap(), 1);
    }

    #[test]
    fn initialize_schema_is_idempotent() {
        let (_tmp, conn) = tmp_db();
        initialize_schema(&conn).unwrap();
        // Running it a second time must not fail or change the version.
        initialize_schema(&conn).unwrap();
        assert_eq!(schema_version(&conn).unwrap(), 1);
    }

    #[test]
    fn foreign_keys_are_enabled() {
        let (_tmp, conn) = tmp_db();
        let fk: i32 = conn
            .pragma_query_value(None, "foreign_keys", |row| row.get(0))
            .unwrap();
        assert_eq!(fk, 1, "foreign_keys PRAGMA should be ON");
    }

    #[test]
    fn rejects_unknown_schema_version() {
        let (_tmp, conn) = tmp_db();
        // Manually set a future version.
        conn.pragma_update(None, "user_version", 99u32).unwrap();
        let result = initialize_schema(&conn);
        assert!(result.is_err());
        assert!(
            result.unwrap_err().to_string().contains("Unsupported"),
            "should mention unsupported version"
        );
    }

    // -----------------------------------------------------------------------
    // Task 3.2 – reopening, data preservation, failure cases
    // -----------------------------------------------------------------------

    #[test]
    fn reopen_preserves_schema_version() {
        // Initialize a library, drop the connection, reopen it, and
        // confirm the schema version is still 1.
        let tmp = TempDir::new().unwrap();
        {
            let conn = open_db(tmp.path()).unwrap();
            initialize_schema(&conn).unwrap();
        } // conn dropped – database closed

        let conn2 = open_db(tmp.path()).unwrap();
        assert_eq!(schema_version(&conn2).unwrap(), 1);
    }

    #[test]
    fn reopen_preserves_inserted_data() {
        // Write a row into `entries`, close the connection, reopen, and
        // verify the row survived.
        let tmp = TempDir::new().unwrap();
        {
            let conn = open_db(tmp.path()).unwrap();
            initialize_schema(&conn).unwrap();
            conn.execute(
                "INSERT INTO entries (entry_id, bibtex_key, title, year, authors_json, raw_bibtex, created_at)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
                rusqlite::params![
                    "fake-uuid",
                    "smith2020",
                    "A Title",
                    2020,
                    "[]",
                    "@article{smith2020, title={A Title}}",
                    "2025-01-01T00:00:00Z",
                ],
            )
            .unwrap();
        } // conn dropped

        let conn2 = open_db(tmp.path()).unwrap();
        let title: String = conn2
            .query_row(
                "SELECT title FROM entries WHERE bibtex_key = ?1",
                ["smith2020"],
                |row| row.get(0),
            )
            .unwrap();
        assert_eq!(title, "A Title");
    }

    #[test]
    fn init_idempotent_preserves_existing_rows() {
        // Ensure that re-running `initialize_schema` on a populated v1
        // database does not delete existing data.
        let tmp = TempDir::new().unwrap();
        let conn = open_db(tmp.path()).unwrap();
        initialize_schema(&conn).unwrap();

        conn.execute(
            "INSERT INTO entries (entry_id, bibtex_key, title, year, authors_json, raw_bibtex, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            rusqlite::params![
                "uuid-1",
                "doe2021",
                "Another Title",
                2021,
                "[]",
                "@article{doe2021, title={Another Title}}",
                "2025-06-01T00:00:00Z",
            ],
        )
        .unwrap();

        // Re-initialize – must be a no-op.
        initialize_schema(&conn).unwrap();

        let count: i64 = conn
            .query_row("SELECT COUNT(*) FROM entries", [], |row| row.get(0))
            .unwrap();
        assert_eq!(count, 1, "row must survive idempotent init");
    }

    #[test]
    fn open_unwritable_path_fails() {
        // Trying to open a DB in a nonexistent directory should fail
        // because rusqlite cannot create intermediate directories.
        let result = open_db(std::path::Path::new(
            "/tmp/papis_rs_test_no_such_dir_xyz/nested",
        ));
        assert!(result.is_err(), "opening a DB in a missing dir should fail");
    }
}
