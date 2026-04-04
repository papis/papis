//! Command handlers for each MVP subcommand.
//!
//! Each `run_*` function is called from `main()` after clap parses the
//! arguments. The handlers orchestrate path resolution, database access,
//! and user-facing output. Actual business logic lives in sibling modules
//! (`db`, `bib`, `storage`, `model`).

use std::path::{Path, PathBuf};

use crate::bib;
use crate::db;
use crate::model::FileRecord;
use crate::storage;

// ---------------------------------------------------------------------------
// Library path helpers
// ---------------------------------------------------------------------------

/// The well-known SQLite database filename inside every library root.
/// Re-exported from `db` for use in this module's validation helpers.
const DB_FILENAME: &str = db::DB_FILENAME;

/// Resolve a user-supplied `--library` path to an absolute path.
///
/// The path is canonicalized when it already exists; otherwise we fall back
/// to joining it with the current working directory so that relative paths
/// like `./my-lib` still become absolute before any I/O.
fn resolve_library_path(raw: &Path) -> anyhow::Result<PathBuf> {
    if raw.exists() {
        // `canonicalize` resolves symlinks and produces an absolute path.
        Ok(raw.canonicalize()?)
    } else {
        // The directory doesn't exist yet (valid for `init`).  Build an
        // absolute path manually so downstream code never works with a
        // relative path.
        let cwd = std::env::current_dir()?;
        Ok(cwd.join(raw))
    }
}

/// Validate that a library root has already been initialized.
///
/// A valid library must be a directory containing the `papis.sqlite3` file.
/// Called by every command *except* `init`.
fn require_initialized_library(library: &Path) -> anyhow::Result<PathBuf> {
    let lib = resolve_library_path(library)?;
    let db_path = lib.join(DB_FILENAME);

    if !lib.is_dir() {
        anyhow::bail!(
            "Library path does not exist or is not a directory: {}",
            lib.display()
        );
    }
    if !db_path.is_file() {
        anyhow::bail!(
            "Library is not initialized (missing {}): {}",
            DB_FILENAME,
            lib.display()
        );
    }
    Ok(lib)
}

// ---------------------------------------------------------------------------
// Command handlers (stubs – filled in by later tasks)
// ---------------------------------------------------------------------------

/// Handle `papis-rs init --library <path>`.
///
/// Creates the library root directory (and parents) if needed, opens or
/// creates `papis.sqlite3`, runs the schema migration, and ensures the
/// `storage/` subdirectory exists.  The whole operation is idempotent.
pub fn run_init(library: &Path) -> anyhow::Result<()> {
    let lib = resolve_library_path(library)?;

    // Create the library root (including parents) if it doesn't exist.
    std::fs::create_dir_all(&lib)?;

    // Create (or open) the SQLite database and apply the v1 schema.
    let conn = db::open_db(&lib)?;
    db::initialize_schema(&conn)?;

    // Ensure the storage/ subdirectory exists for later PDF attachment.
    let storage = lib.join("storage");
    std::fs::create_dir_all(&storage)?;

    println!("Library initialized at {}", lib.display());
    Ok(())
}

/// Handle `papis-rs import-bib --library <path> <file.bib>`.
///
/// Reads the `.bib` file, parses all entries, then inserts them into the
/// library's SQLite database.  Entries whose `bibtex_key` already exists
/// are skipped (not overwritten).  If the BibTeX is syntactically invalid,
/// the command fails without inserting anything.
pub fn run_import_bib(library: &Path, bib_file: &Path) -> anyhow::Result<()> {
    let lib = require_initialized_library(library)?;

    // Read the entire .bib file into memory.
    let src = std::fs::read_to_string(bib_file)
        .map_err(|e| anyhow::anyhow!("Cannot read {}: {e}", bib_file.display()))?;

    // Parse all BibTeX entries (fails on invalid syntax).
    let parsed = bib::parse_bib(&src)?;

    if parsed.entries.is_empty() {
        println!("No entries found in {}", bib_file.display());
        return Ok(());
    }

    // Open the library database and insert the parsed entries.
    let conn = db::open_db(&lib)?;
    let result = db::insert_entries(&conn, &parsed.entries)?;

    // Report results to the user.
    println!("Imported {} entries.", result.inserted);
    if !result.skipped_keys.is_empty() {
        println!(
            "Skipped {} duplicate key(s): {}",
            result.skipped_keys.len(),
            result.skipped_keys.join(", ")
        );
    }
    // Also report in-file duplicates detected during parsing.
    if !parsed.duplicate_keys.is_empty() {
        println!(
            "Skipped {} in-file duplicate key(s): {}",
            parsed.duplicate_keys.len(),
            parsed.duplicate_keys.join(", ")
        );
    }

    Ok(())
}

/// Handle `papis-rs add-pdf --library <path> <bibtex_key> <file.pdf>`.
///
/// Attaches a PDF to an existing library entry.  The command:
/// 1. Validates that the source file exists and starts with `%PDF-`.
/// 2. Looks up the entry by `bibtex_key` (fails if not found).
/// 3. Computes the SHA-256 hash of the source file.
/// 4. Copies the file to `<library>/storage/<entry_id>/main.pdf`.
/// 5. Records a row in the `files` table with the relative path, hash,
///    and MIME type.
///
/// No partial writes: if any step fails, nothing is committed to the DB.
pub fn run_add_pdf(library: &Path, bibtex_key: &str, pdf_file: &Path) -> anyhow::Result<()> {
    let lib = require_initialized_library(library)?;

    // 1. Validate the source PDF (existence + magic bytes).
    storage::validate_pdf(pdf_file)?;

    // 2. Find the entry this PDF should be attached to.
    let conn = db::open_db(&lib)?;
    let entry = db::find_entry_by_key(&conn, bibtex_key)?
        .ok_or_else(|| anyhow::anyhow!("No entry found with bibtex_key '{bibtex_key}'"))?;

    // 3. Hash the source file before copying.
    let sha256 = storage::sha256_file(pdf_file)?;

    // 4. Copy the PDF into the library storage directory.
    let stored_relpath = storage::copy_pdf_to_storage(&lib, &entry.entry_id, pdf_file)?;

    // 5. Record the attachment in the database.
    let file_record = FileRecord {
        file_id: uuid::Uuid::new_v4().to_string(),
        entry_id: entry.entry_id.clone(),
        role: "main".to_string(),
        stored_relpath: stored_relpath.clone(),
        source_path: pdf_file.display().to_string(),
        sha256,
        mime: "application/pdf".to_string(),
    };
    db::insert_file(&conn, &file_record)?;

    println!("Attached PDF to '{}' → {}", bibtex_key, stored_relpath);
    Ok(())
}

/// Handle `papis-rs list --library <path>`.
///
/// Prints a one-line summary for every entry in the library, ordered by
/// `bibtex_key`.  If the library is empty, prints a friendly message
/// instead of blank output.
pub fn run_list(library: &Path) -> anyhow::Result<()> {
    let lib = require_initialized_library(library)?;
    let conn = db::open_db(&lib)?;

    let entries = db::list_entries(&conn)?;

    if entries.is_empty() {
        println!("No entries in the library.");
        return Ok(());
    }

    for entry in &entries {
        // Format: "bibtex_key  Title (year)" or "bibtex_key  Title" if no year.
        let title = entry.title.as_deref().unwrap_or("(no title)");
        match entry.year {
            Some(y) => println!("{}  {} ({})", entry.bibtex_key, title, y),
            None => println!("{}  {}", entry.bibtex_key, title),
        }
    }

    Ok(())
}

/// Handle `papis-rs show --library <path> <bibtex_key>`.
///
/// Displays the full stored metadata for one entry, plus a list of any
/// attached files.  Fails with a clear error if the key is not found.
pub fn run_show(library: &Path, bibtex_key: &str) -> anyhow::Result<()> {
    let lib = require_initialized_library(library)?;
    let conn = db::open_db(&lib)?;

    let entry = db::find_entry_by_key(&conn, bibtex_key)?
        .ok_or_else(|| anyhow::anyhow!("No entry found with bibtex_key '{bibtex_key}'"))?;

    // Header: key and title.
    println!("Key:     {}", entry.bibtex_key);
    println!(
        "Title:   {}",
        entry.title.as_deref().unwrap_or("(no title)")
    );
    if let Some(y) = entry.year {
        println!("Year:    {y}");
    }
    println!("Authors: {}", entry.authors_json);
    println!("Created: {}", entry.created_at);

    // Attached files section.
    let files = db::files_for_entry(&conn, &entry.entry_id)?;
    if files.is_empty() {
        println!("\nNo attached files.");
    } else {
        println!("\nAttached files:");
        for f in &files {
            println!("  [{}] {} (sha256: {})", f.role, f.stored_relpath, f.sha256);
        }
    }

    Ok(())
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn resolve_existing_path_returns_absolute() {
        let tmp = TempDir::new().unwrap();
        let resolved = resolve_library_path(tmp.path()).unwrap();
        assert!(resolved.is_absolute());
    }

    #[test]
    fn resolve_nonexistent_path_returns_absolute() {
        let resolved = resolve_library_path(Path::new("does-not-exist")).unwrap();
        assert!(resolved.is_absolute());
    }

    #[test]
    fn require_initialized_fails_for_missing_dir() {
        let result = require_initialized_library(Path::new("/tmp/no-such-library-xyz"));
        assert!(result.is_err());
    }

    #[test]
    fn require_initialized_fails_for_dir_without_db() {
        let tmp = TempDir::new().unwrap();
        let result = require_initialized_library(tmp.path());
        assert!(result.is_err());
        let msg = result.unwrap_err().to_string();
        assert!(msg.contains("not initialized"), "unexpected error: {msg}");
    }

    #[test]
    fn require_initialized_succeeds_with_db_file() {
        let tmp = TempDir::new().unwrap();
        // Create a dummy papis.sqlite3 so the check passes.
        std::fs::write(tmp.path().join(DB_FILENAME), b"").unwrap();
        let lib = require_initialized_library(tmp.path()).unwrap();
        assert!(lib.is_absolute());
    }
}

// ---------------------------------------------------------------------------
// End-to-end tests
// ---------------------------------------------------------------------------
//
// These exercise the full init → import-bib → add-pdf → list → show
// workflow using temporary directories. Each test creates a fresh library
// from scratch and calls the public `run_*` handlers, verifying both the
// database state and the file system.

#[cfg(test)]
mod e2e_tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    /// Sample BibTeX with two entries for E2E tests.
    const SAMPLE_BIB: &str = r#"
@article{smith2020,
    author = {Smith, John},
    title  = {A Great Paper},
    year   = {2020},
}
@inproceedings{doe2021,
    author = {Doe, Jane},
    title  = {Another Study},
    year   = {2021},
}
"#;

    /// Create a fake PDF file that passes magic-byte validation.
    fn write_fake_pdf(path: &std::path::Path) {
        fs::write(path, b"%PDF-1.7 fake content for e2e testing").unwrap();
    }

    // --- init ---

    #[test]
    fn e2e_init_creates_db_and_storage() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("my-library");

        run_init(&lib).unwrap();

        assert!(lib.join("papis.sqlite3").is_file());
        assert!(lib.join("storage").is_dir());
    }

    #[test]
    fn e2e_init_is_idempotent() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");

        run_init(&lib).unwrap();
        // Second init must not fail or lose data.
        run_init(&lib).unwrap();

        assert!(lib.join("papis.sqlite3").is_file());
    }

    // --- import-bib ---

    #[test]
    fn e2e_import_bib_stores_entries() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        let bib_path = tmp.path().join("refs.bib");
        fs::write(&bib_path, SAMPLE_BIB).unwrap();

        run_import_bib(&lib, &bib_path).unwrap();

        // Verify both entries are in the database.
        let conn = db::open_db(&lib).unwrap();
        let entries = db::list_entries(&conn).unwrap();
        assert_eq!(entries.len(), 2);

        let keys: Vec<&str> = entries.iter().map(|e| e.bibtex_key.as_str()).collect();
        assert!(keys.contains(&"smith2020"));
        assert!(keys.contains(&"doe2021"));
    }

    #[test]
    fn e2e_import_bib_skips_duplicates() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        let bib_path = tmp.path().join("refs.bib");
        fs::write(&bib_path, SAMPLE_BIB).unwrap();

        // Import twice – second run should skip all entries.
        run_import_bib(&lib, &bib_path).unwrap();
        run_import_bib(&lib, &bib_path).unwrap();

        let conn = db::open_db(&lib).unwrap();
        let entries = db::list_entries(&conn).unwrap();
        // Still exactly 2, not 4.
        assert_eq!(entries.len(), 2);
    }

    #[test]
    fn e2e_import_invalid_bib_fails_cleanly() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        let bad_bib = tmp.path().join("bad.bib");
        fs::write(&bad_bib, "@article{broken, title =").unwrap();

        let result = run_import_bib(&lib, &bad_bib);
        assert!(result.is_err());

        // No entries should have been inserted.
        let conn = db::open_db(&lib).unwrap();
        let entries = db::list_entries(&conn).unwrap();
        assert!(entries.is_empty());
    }

    // --- add-pdf ---

    #[test]
    fn e2e_add_pdf_copies_and_records_file() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        // Import an entry first.
        let bib_path = tmp.path().join("refs.bib");
        fs::write(&bib_path, SAMPLE_BIB).unwrap();
        run_import_bib(&lib, &bib_path).unwrap();

        // Create a fake PDF and attach it.
        let pdf_path = tmp.path().join("paper.pdf");
        write_fake_pdf(&pdf_path);

        run_add_pdf(&lib, "smith2020", &pdf_path).unwrap();

        // The file should exist in storage.
        let conn = db::open_db(&lib).unwrap();
        let entry = db::find_entry_by_key(&conn, "smith2020").unwrap().unwrap();
        let files = db::files_for_entry(&conn, &entry.entry_id).unwrap();
        assert_eq!(files.len(), 1);
        assert_eq!(files[0].role, "main");
        assert_eq!(files[0].mime, "application/pdf");

        // Physical file should exist.
        let stored = lib.join(&files[0].stored_relpath);
        assert!(stored.is_file());
    }

    #[test]
    fn e2e_add_pdf_rejects_missing_file() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        let bib_path = tmp.path().join("refs.bib");
        fs::write(&bib_path, SAMPLE_BIB).unwrap();
        run_import_bib(&lib, &bib_path).unwrap();

        let result = run_add_pdf(&lib, "smith2020", Path::new("/tmp/no-such-file.pdf"));
        assert!(result.is_err());
    }

    #[test]
    fn e2e_add_pdf_rejects_non_pdf() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        let bib_path = tmp.path().join("refs.bib");
        fs::write(&bib_path, SAMPLE_BIB).unwrap();
        run_import_bib(&lib, &bib_path).unwrap();

        let txt = tmp.path().join("notes.txt");
        fs::write(&txt, "not a pdf").unwrap();

        let result = run_add_pdf(&lib, "smith2020", &txt);
        assert!(result.is_err());

        // No files row should have been created.
        let conn = db::open_db(&lib).unwrap();
        let entry = db::find_entry_by_key(&conn, "smith2020").unwrap().unwrap();
        let files = db::files_for_entry(&conn, &entry.entry_id).unwrap();
        assert!(files.is_empty());
    }

    #[test]
    fn e2e_add_pdf_rejects_unknown_key() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        let pdf = tmp.path().join("paper.pdf");
        write_fake_pdf(&pdf);

        let result = run_add_pdf(&lib, "nonexistent_key", &pdf);
        assert!(result.is_err());
        let msg = result.unwrap_err().to_string();
        assert!(
            msg.contains("nonexistent_key"),
            "error should mention the key: {msg}"
        );
    }

    // --- list ---

    #[test]
    fn e2e_list_empty_library_succeeds() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        // Should not fail on an empty library.
        run_list(&lib).unwrap();
    }

    #[test]
    fn e2e_list_after_import_succeeds() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        let bib_path = tmp.path().join("refs.bib");
        fs::write(&bib_path, SAMPLE_BIB).unwrap();
        run_import_bib(&lib, &bib_path).unwrap();

        run_list(&lib).unwrap();
    }

    // --- show ---

    #[test]
    fn e2e_show_entry_without_files() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        let bib_path = tmp.path().join("refs.bib");
        fs::write(&bib_path, SAMPLE_BIB).unwrap();
        run_import_bib(&lib, &bib_path).unwrap();

        // show should succeed even without attached files.
        run_show(&lib, "smith2020").unwrap();
    }

    #[test]
    fn e2e_show_entry_with_pdf() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        let bib_path = tmp.path().join("refs.bib");
        fs::write(&bib_path, SAMPLE_BIB).unwrap();
        run_import_bib(&lib, &bib_path).unwrap();

        let pdf = tmp.path().join("paper.pdf");
        write_fake_pdf(&pdf);
        run_add_pdf(&lib, "doe2021", &pdf).unwrap();

        // show should display the attached file info.
        run_show(&lib, "doe2021").unwrap();
    }

    #[test]
    fn e2e_show_unknown_key_fails() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        run_init(&lib).unwrap();

        let result = run_show(&lib, "ghost_key");
        assert!(result.is_err());
        let msg = result.unwrap_err().to_string();
        assert!(
            msg.contains("ghost_key"),
            "error should mention the key: {msg}"
        );
    }

    // --- full workflow ---

    #[test]
    fn e2e_full_init_import_add_pdf_list_show() {
        // Exercises the entire MVP pipeline in a single test.
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");

        // 1. Init
        run_init(&lib).unwrap();

        // 2. Import BibTeX
        let bib_path = tmp.path().join("refs.bib");
        fs::write(&bib_path, SAMPLE_BIB).unwrap();
        run_import_bib(&lib, &bib_path).unwrap();

        // 3. Attach PDF to one entry
        let pdf = tmp.path().join("paper.pdf");
        write_fake_pdf(&pdf);
        run_add_pdf(&lib, "smith2020", &pdf).unwrap();

        // 4. List
        run_list(&lib).unwrap();

        // 5. Show entry with PDF
        run_show(&lib, "smith2020").unwrap();

        // 6. Show entry without PDF
        run_show(&lib, "doe2021").unwrap();

        // Verify final database state.
        let conn = db::open_db(&lib).unwrap();
        let entries = db::list_entries(&conn).unwrap();
        assert_eq!(entries.len(), 2);

        let smith = db::find_entry_by_key(&conn, "smith2020").unwrap().unwrap();
        let smith_files = db::files_for_entry(&conn, &smith.entry_id).unwrap();
        assert_eq!(smith_files.len(), 1);

        let doe = db::find_entry_by_key(&conn, "doe2021").unwrap().unwrap();
        let doe_files = db::files_for_entry(&conn, &doe.entry_id).unwrap();
        assert!(doe_files.is_empty());
    }
}
