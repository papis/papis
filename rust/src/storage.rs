//! File storage: PDF validation, SHA-256 hashing, and deterministic
//! copy of attached files into `<library>/storage/<entry_id>/`.
//!
//! The storage layout is:
//!
//! ```text
//! <library>/
//!   storage/
//!     <entry_id>/
//!       main.pdf          ← the one file allowed per entry in the MVP
//! ```
//!
//! Every function in this module is a pure helper – no database I/O happens
//! here.  The CLI handler (`cli::run_add_pdf`) orchestrates calls between
//! `db` and `storage`.

use std::fs;
use std::io::Read;
use std::path::Path;

use sha2::{Digest, Sha256};

/// The first 5 bytes of every valid PDF file: `%PDF-` (ASCII).
const PDF_MAGIC: &[u8] = b"%PDF-";

/// The well-known filename for the single main attachment in the MVP.
const MAIN_PDF_FILENAME: &str = "main.pdf";

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/// Validate that the file at `path` looks like a real PDF.
///
/// The check reads only the first 5 bytes and verifies they match the
/// `%PDF-` magic number.  This catches obviously-wrong files (plain text,
/// images, etc.) without pulling the whole file into memory.
pub fn validate_pdf(path: &Path) -> anyhow::Result<()> {
    let mut f = fs::File::open(path)
        .map_err(|e| anyhow::anyhow!("Cannot open file {}: {e}", path.display()))?;

    let mut magic = [0u8; 5];
    let n = f
        .read(&mut magic)
        .map_err(|e| anyhow::anyhow!("Cannot read file {}: {e}", path.display()))?;

    if n < PDF_MAGIC.len() || &magic[..PDF_MAGIC.len()] != PDF_MAGIC {
        anyhow::bail!(
            "File does not appear to be a valid PDF (bad magic bytes): {}",
            path.display()
        );
    }

    Ok(())
}

/// Compute the hex-encoded SHA-256 digest of a file.
///
/// Reads the file in 8 KiB chunks so that large PDFs don't need to fit
/// entirely in memory.
pub fn sha256_file(path: &Path) -> anyhow::Result<String> {
    let mut f = fs::File::open(path)
        .map_err(|e| anyhow::anyhow!("Cannot open file for hashing {}: {e}", path.display()))?;

    let mut hasher = Sha256::new();
    let mut buf = [0u8; 8192];

    loop {
        let n = f.read(&mut buf)?;
        if n == 0 {
            break;
        }
        hasher.update(&buf[..n]);
    }

    // `finalize` returns a fixed-size array; format each byte as lowercase
    // hex to get the canonical 64-character string.
    let digest = hasher.finalize();
    Ok(hex_encode(&digest))
}

/// Copy `source` into the entry's storage directory:
/// `<library>/storage/<entry_id>/main.pdf`
///
/// Creates the per-entry directory if it doesn't exist.  Returns the
/// relative path from the library root (e.g. `storage/<entry_id>/main.pdf`)
/// which is what we store in the `files` table's `stored_relpath` column.
pub fn copy_pdf_to_storage(
    library: &Path,
    entry_id: &str,
    source: &Path,
) -> anyhow::Result<String> {
    // Build the destination directory: <library>/storage/<entry_id>/
    let entry_dir = library.join("storage").join(entry_id);
    fs::create_dir_all(&entry_dir)?;

    let dest = entry_dir.join(MAIN_PDF_FILENAME);
    fs::copy(source, &dest)
        .map_err(|e| anyhow::anyhow!("Failed to copy PDF to {}: {e}", dest.display()))?;

    // Build the portable relative path for the database.
    // We always use forward-slash separators regardless of OS.
    let relpath = format!("storage/{entry_id}/{MAIN_PDF_FILENAME}");
    Ok(relpath)
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/// Encode a byte slice as a lowercase hex string.
///
/// We roll our own rather than pulling in a `hex` crate for this one-liner.
fn hex_encode(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for &b in bytes {
        use std::fmt::Write;
        // write! to a String never fails, so unwrap is safe.
        write!(s, "{b:02x}").unwrap();
    }
    s
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use std::path::PathBuf;
    use tempfile::TempDir;

    /// Create a temporary file that starts with the PDF magic bytes
    /// followed by some filler content.
    fn make_fake_pdf(dir: &Path, name: &str) -> PathBuf {
        let path = dir.join(name);
        let mut f = fs::File::create(&path).unwrap();
        // Real PDFs start with %PDF-1.x; we just need the magic prefix.
        f.write_all(b"%PDF-1.7 fake content for testing").unwrap();
        path
    }

    /// Create a non-PDF file for negative tests.
    fn make_non_pdf(dir: &Path, name: &str) -> PathBuf {
        let path = dir.join(name);
        fs::write(&path, b"This is plain text, not a PDF.").unwrap();
        path
    }

    // --- validate_pdf ---

    #[test]
    fn validate_pdf_accepts_valid_magic() {
        let tmp = TempDir::new().unwrap();
        let pdf = make_fake_pdf(tmp.path(), "good.pdf");
        assert!(validate_pdf(&pdf).is_ok());
    }

    #[test]
    fn validate_pdf_rejects_non_pdf() {
        let tmp = TempDir::new().unwrap();
        let txt = make_non_pdf(tmp.path(), "bad.txt");
        let err = validate_pdf(&txt).unwrap_err();
        assert!(
            err.to_string().contains("bad magic bytes"),
            "unexpected error: {err}"
        );
    }

    #[test]
    fn validate_pdf_rejects_missing_file() {
        let result = validate_pdf(Path::new("/tmp/no-such-file-xyz.pdf"));
        assert!(result.is_err());
    }

    #[test]
    fn validate_pdf_rejects_empty_file() {
        let tmp = TempDir::new().unwrap();
        let path = tmp.path().join("empty.pdf");
        fs::write(&path, b"").unwrap();
        let err = validate_pdf(&path).unwrap_err();
        assert!(
            err.to_string().contains("bad magic bytes"),
            "unexpected error: {err}"
        );
    }

    // --- sha256_file ---

    #[test]
    fn sha256_known_value() {
        // SHA-256 of the empty string is a well-known constant.
        let tmp = TempDir::new().unwrap();
        let path = tmp.path().join("empty");
        fs::write(&path, b"").unwrap();

        let hash = sha256_file(&path).unwrap();
        assert_eq!(
            hash,
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
    }

    #[test]
    fn sha256_nonempty_file() {
        let tmp = TempDir::new().unwrap();
        let pdf = make_fake_pdf(tmp.path(), "test.pdf");

        let hash = sha256_file(&pdf).unwrap();
        // Just check the shape: 64 lowercase hex characters.
        assert_eq!(hash.len(), 64);
        assert!(hash.chars().all(|c| c.is_ascii_hexdigit()));
    }

    #[test]
    fn sha256_missing_file_errors() {
        let result = sha256_file(Path::new("/tmp/no-such-hash-target.pdf"));
        assert!(result.is_err());
    }

    // --- copy_pdf_to_storage ---

    #[test]
    fn copy_creates_entry_dir_and_copies_file() {
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        fs::create_dir_all(lib.join("storage")).unwrap();

        let source = make_fake_pdf(tmp.path(), "paper.pdf");

        let relpath = copy_pdf_to_storage(&lib, "entry-uuid-1", &source).unwrap();
        assert_eq!(relpath, "storage/entry-uuid-1/main.pdf");

        // The destination file should exist and match the source.
        let dest = lib.join(&relpath);
        assert!(dest.is_file());
        assert_eq!(fs::read(&dest).unwrap(), fs::read(&source).unwrap());
    }

    #[test]
    fn copy_overwrites_existing_main_pdf() {
        // If a user re-runs add-pdf, the copy should overwrite cleanly.
        let tmp = TempDir::new().unwrap();
        let lib = tmp.path().join("lib");
        fs::create_dir_all(lib.join("storage")).unwrap();

        let v1 = make_fake_pdf(tmp.path(), "v1.pdf");
        copy_pdf_to_storage(&lib, "entry-uuid-2", &v1).unwrap();

        // Write a different "PDF" and copy again.
        let v2_path = tmp.path().join("v2.pdf");
        fs::write(&v2_path, b"%PDF-2.0 updated").unwrap();
        copy_pdf_to_storage(&lib, "entry-uuid-2", &v2_path).unwrap();

        let stored = fs::read(lib.join("storage/entry-uuid-2/main.pdf")).unwrap();
        assert_eq!(stored, b"%PDF-2.0 updated");
    }

    // --- hex_encode ---

    #[test]
    fn hex_encode_empty() {
        assert_eq!(hex_encode(&[]), "");
    }

    #[test]
    fn hex_encode_known() {
        assert_eq!(hex_encode(&[0x00, 0xff, 0xab, 0x12]), "00ffab12");
    }
}
