//! BibTeX parsing and mapping: reads `.bib` files and converts entries
//! into the internal `Entry` model used by the database layer.
//!
//! The parsing strategy is "all-or-nothing for syntax":
//! - If the BibTeX is syntactically invalid, the entire import fails.
//! - If a file contains duplicate keys, only the first occurrence is kept
//!   and duplicates are reported for upstream handling.

use biblatex::{Bibliography, ChunksExt, DateValue, PermissiveType, Person, RetrievalError};

use crate::model::{Author, Entry};

/// The result of parsing a `.bib` file.
///
/// Contains the list of parsed entries and any BibTeX keys that appeared
/// more than once within the same file (only the first occurrence is kept).
pub struct ParsedBib {
    /// Successfully parsed entries (one per unique `bibtex_key`).
    pub entries: Vec<Entry>,
    /// Keys that were seen more than once in the input file.
    pub duplicate_keys: Vec<String>,
}

/// Parse a BibTeX string and convert all entries into our `Entry` model.
///
/// Returns an error if the input is syntactically invalid.  Within a
/// valid file, duplicate `bibtex_key` values are deduplicated (first
/// occurrence wins) and reported in `ParsedBib::duplicate_keys`.
pub fn parse_bib(src: &str) -> anyhow::Result<ParsedBib> {
    // The biblatex crate returns a Result; a parse error means the
    // entire file is syntactically invalid.
    let bibliography =
        Bibliography::parse(src).map_err(|e| anyhow::anyhow!("Invalid BibTeX: {e}"))?;

    let now = chrono_now_utc();

    let mut entries = Vec::new();
    let mut seen_keys = std::collections::HashSet::new();
    let mut duplicate_keys = Vec::new();

    for entry in bibliography.iter() {
        let key = entry.key.clone();

        // Deduplicate within the same file: first occurrence wins.
        if !seen_keys.insert(key.clone()) {
            duplicate_keys.push(key);
            continue;
        }

        // --- Extract title (optional) ---
        // `format_verbatim()` from `ChunksExt` gives us plain text
        // without BibTeX markup (braces, commands, etc.).
        let title = match entry.title() {
            Ok(chunks) => Some(chunks.format_verbatim()),
            Err(RetrievalError::Missing(_)) => None,
            Err(e) => {
                // A type error in the title field – fall back to None and
                // let the rest of the entry import proceed.
                eprintln!("Warning: could not parse title for {key}: {e}");
                None
            }
        };

        // --- Extract year (optional) ---
        // The biblatex crate exposes `date()` which merges the `date`,
        // `year`, `month`, and `day` fields.  We only need the year.
        let year = extract_year(entry);

        // --- Extract authors ---
        let authors_json = match entry.author() {
            Ok(persons) => {
                let authors: Vec<Author> = persons
                    .iter()
                    .map(|p: &Person| Author {
                        name: p.name.clone(),
                        given_name: p.given_name.clone(),
                        prefix: p.prefix.clone(),
                        suffix: p.suffix.clone(),
                    })
                    .collect();
                serde_json::to_string(&authors)?
            }
            Err(_) => "[]".to_string(),
        };

        // --- Raw BibTeX text ---
        // `to_biblatex_string()` produces a normalized representation.
        let raw_bibtex = entry.to_biblatex_string();

        entries.push(Entry {
            entry_id: uuid::Uuid::new_v4().to_string(),
            bibtex_key: key,
            title,
            year,
            authors_json,
            raw_bibtex,
            created_at: now.clone(),
        });
    }

    Ok(ParsedBib {
        entries,
        duplicate_keys,
    })
}

/// Try to extract a year as `i32` from a biblatex `Entry`.
///
/// The `date()` method returns a `PermissiveType<Date>` which can be a
/// proper typed date or a raw string (e.g. "forthcoming").  We only
/// extract the year from typed, single-date values.
fn extract_year(entry: &biblatex::Entry) -> Option<i32> {
    match entry.date() {
        Ok(PermissiveType::Typed(date)) => {
            // `DateValue` can be a single date or a range.
            // For MVP we only care about the start date's year.
            match date.value {
                DateValue::At(datetime)
                | DateValue::After(datetime)
                | DateValue::Before(datetime) => Some(datetime.year),
                DateValue::Between(start, _end) => Some(start.year),
            }
        }
        // PermissiveType::Chunks means the date was a raw string the
        // parser couldn't interpret as a structured date.  Skip it.
        _ => None,
    }
}

/// Return the current UTC time as an ISO-8601 string.
///
/// Uses a simple manual approach to avoid pulling in a full datetime crate
/// for MVP.  The format matches "YYYY-MM-DDTHH:MM:SSZ".
fn chrono_now_utc() -> String {
    // `SystemTime` gives us seconds since UNIX epoch.  We format a
    // simplified UTC timestamp without pulling in the `chrono` crate.
    use std::time::SystemTime;
    let duration = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .expect("system clock before UNIX epoch");
    let secs = duration.as_secs();

    // Simple calendar arithmetic (no leap-second precision needed).
    let days = secs / 86400;
    let time_of_day = secs % 86400;
    let hours = time_of_day / 3600;
    let minutes = (time_of_day % 3600) / 60;
    let seconds = time_of_day % 60;

    // Convert days since epoch to year-month-day.
    let (year, month, day) = days_to_ymd(days);

    format!("{year:04}-{month:02}-{day:02}T{hours:02}:{minutes:02}:{seconds:02}Z")
}

/// Convert days since the UNIX epoch (1970-01-01) to (year, month, day).
fn days_to_ymd(mut days: u64) -> (u64, u64, u64) {
    let mut year = 1970;
    loop {
        let days_in_year = if is_leap(year) { 366 } else { 365 };
        if days < days_in_year {
            break;
        }
        days -= days_in_year;
        year += 1;
    }

    let leap = is_leap(year);
    let month_days: [u64; 12] = [
        31,
        if leap { 29 } else { 28 },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ];
    let mut month = 1;
    for &md in &month_days {
        if days < md {
            break;
        }
        days -= md;
        month += 1;
    }

    (year, month, days + 1)
}

fn is_leap(y: u64) -> bool {
    y.is_multiple_of(4) && (!y.is_multiple_of(100) || y.is_multiple_of(400))
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    const SAMPLE_BIB: &str = r#"
@article{smith2020,
    author = {Alice Smith and Bob Jones},
    title = {A Great Paper},
    year = {2020},
    journal = {Some Journal},
}

@book{doe2019,
    author = {Jane Doe},
    title = {An Important Book},
    year = {2019},
    publisher = {Acme Press},
}
"#;

    #[test]
    fn parse_valid_bib_extracts_entries() {
        let result = parse_bib(SAMPLE_BIB).unwrap();
        assert_eq!(result.entries.len(), 2);
        assert!(result.duplicate_keys.is_empty());

        let smith = result
            .entries
            .iter()
            .find(|e| e.bibtex_key == "smith2020")
            .unwrap();
        assert_eq!(smith.title.as_deref(), Some("A Great Paper"));
        assert_eq!(smith.year, Some(2020));

        // Verify authors_json is valid JSON containing both authors.
        let authors: Vec<Author> = serde_json::from_str(&smith.authors_json).unwrap();
        assert_eq!(authors.len(), 2);
        assert_eq!(authors[0].name, "Smith");
        assert_eq!(authors[1].name, "Jones");
    }

    #[test]
    fn parse_duplicate_keys_in_file_is_a_parse_error() {
        // The biblatex crate rejects files with duplicate citation keys
        // at parse time, so this results in an error (not dedup).
        let bib = r#"
@article{dup2020,
    author = {A},
    title = {First},
    year = {2020},
}
@article{dup2020,
    author = {B},
    title = {Second},
    year = {2021},
}
"#;
        let result = parse_bib(bib);
        assert!(
            result.is_err(),
            "in-file duplicate keys should be a parse error"
        );
    }

    #[test]
    fn parse_truly_invalid_bib_returns_error() {
        // Unbalanced braces produce a parse error in the biblatex crate.
        let result = parse_bib("@article{key, title = {unterminated");
        assert!(result.is_err());
    }

    #[test]
    fn parse_nonsense_text_produces_zero_entries() {
        // Plain text without @ entries parses "successfully" but yields
        // nothing.  This is valid biblatex behavior (comments are allowed).
        let result = parse_bib("hello world").unwrap();
        assert!(result.entries.is_empty());
    }

    #[test]
    fn entry_ids_are_unique_uuids() {
        let result = parse_bib(SAMPLE_BIB).unwrap();
        assert_ne!(result.entries[0].entry_id, result.entries[1].entry_id);
        // Quick sanity check that it looks like a UUID (36 chars with dashes).
        assert_eq!(result.entries[0].entry_id.len(), 36);
    }

    #[test]
    fn entry_without_title_maps_to_none() {
        let bib = r#"
@misc{notitle2020,
    author = {Someone},
    year = {2020},
}
"#;
        let result = parse_bib(bib).unwrap();
        assert_eq!(result.entries.len(), 1);
        assert!(result.entries[0].title.is_none());
    }

    #[test]
    fn entry_without_year_maps_to_none() {
        let bib = r#"
@misc{noyear,
    author = {Someone},
    title = {A Thing},
}
"#;
        let result = parse_bib(bib).unwrap();
        assert_eq!(result.entries.len(), 1);
        assert!(result.entries[0].year.is_none());
    }
}
