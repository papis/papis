//! Data models: plain Rust structs representing library entries and
//! attached files. These are the shared types passed between modules.

use serde::{Deserialize, Serialize};

/// A library entry imported from a BibTeX source.
///
/// Corresponds to the `entries` table in the SQLite schema.  The
/// `entry_id` is a UUID generated at import time; `bibtex_key` is the
/// human-facing identifier used in CLI commands like `show` and `add-pdf`.
#[derive(Debug, Clone)]
pub struct Entry {
    /// Internal UUID primary key (generated, not user-visible in MVP).
    pub entry_id: String,
    /// The BibTeX citation key, e.g. "smith2020".  Unique across the library.
    pub bibtex_key: String,
    /// The title of the work (may be `None` if the BibTeX entry has no title).
    pub title: Option<String>,
    /// Publication year (may be `None` if the BibTeX entry has no date/year).
    pub year: Option<i32>,
    /// JSON-encoded array of author objects, each with `name`, `given_name`,
    /// `prefix`, and `suffix` fields.  Empty array `"[]"` if no authors.
    pub authors_json: String,
    /// The raw BibTeX source text for this entry (normalized by the parser).
    pub raw_bibtex: String,
    /// ISO-8601 creation timestamp, e.g. "2025-01-01T00:00:00Z".
    pub created_at: String,
}

/// An attached file (typically a PDF) linked to a library entry.
///
/// Corresponds to the `files` table in the SQLite schema.
#[derive(Debug, Clone)]
pub struct FileRecord {
    /// Internal UUID primary key for this file record.
    pub file_id: String,
    /// The `entry_id` this file belongs to.
    pub entry_id: String,
    /// The role of the attachment, e.g. "main".
    pub role: String,
    /// Relative path from the library root, e.g. "storage/<entry_id>/main.pdf".
    pub stored_relpath: String,
    /// The original source path provided by the user.
    pub source_path: String,
    /// Hex-encoded SHA-256 hash of the file contents.
    pub sha256: String,
    /// MIME type, e.g. "application/pdf".
    pub mime: String,
}

/// Lightweight author representation used inside `authors_json`.
///
/// Serialized as a JSON array of these objects.  The fields mirror the
/// `Person` struct from the `biblatex` crate so we capture what the
/// parser gives us without inventing extra normalization.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Author {
    /// Family name (surname).
    pub name: String,
    /// Given (first) name, if present.
    pub given_name: String,
    /// Name prefix (e.g. "von", "de"), if present.
    pub prefix: String,
    /// Name suffix (e.g. "Jr.", "III"), if present.
    pub suffix: String,
}
