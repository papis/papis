# Lessons Learnt — `add-mvp-cli-entry-points`

Mistakes encountered during the implementation of the MVP CLI and how each was resolved.

---

## 1. `Bibliography::parse` returns `Result`, not `Option`

**Mistake:** Initially used `.ok_or_else()` on the return value of `Bibliography::parse(src)`, as if it returned an `Option`. The `biblatex` crate's `parse` method actually returns `Result<Self, ParseError>`.

**Symptom:** Compilation error — `.ok_or_else()` is not defined for `Result`.

**Fix:** Changed to `.map_err(|e| anyhow::anyhow!("Invalid BibTeX: {e}"))` which correctly transforms the `Err` variant.

---

## 2. `ChunksExt` type confusion — `to_biblatex_string()` vs `format_verbatim()`

**Mistake:** Tried to call `to_biblatex_string()` on `ChunksRef` (the return from `entry.title()`) to get the plain-text title. That method requires a boolean `is_verbatim` parameter and is intended for round-tripping, not for display.

**Symptom:** Type mismatch error at compile time.

**Fix:** Switched to `chunks.format_verbatim()` from the `ChunksExt` trait, which returns a plain `String` without BibTeX markup — the right tool for extracting display text.

---

## 3. Missing explicit type annotation on `Person` closure parameter

**Mistake:** Wrote `.map(|p| Author { name: p.name.clone(), ... })` without annotating the type of `p`. The compiler couldn't infer the type through the iterator chain.

**Symptom:** "type annotations needed" compiler error.

**Fix:** Added the explicit type: `.map(|p: &Person| Author { ... })`.

---

## 4. Misunderstanding biblatex crate's duplicate-key handling

**Mistake:** Wrote a test assuming that duplicate `bibtex_key` values *within the same file* would be silently deduplicated by the `biblatex` crate and reported by our code. In reality, the crate rejects in-file duplicate keys at parse time — `Bibliography::parse` returns `Err`.

**Symptom:** Test expected 1 entry from a file with duplicate keys, but `parse` returned a parse error instead.

**Fix:** Changed the test to assert that a parse error is returned (not a dedup result). Added a separate test confirming that nonsense text without `@` entries parses "successfully" with 0 entries. Cross-library dedup (re-importing the same key) is handled at the SQLite layer via `INSERT OR IGNORE`.

---

## 5. Stale `[build]` key in `Cargo.toml`

**Mistake:** The original `Cargo.toml` had a `[build] target-dir = "target"` section that produced a Cargo warning.

**Symptom:** `cargo build` printed a deprecation/warning about the `[build]` key.

**Fix:** Removed the `[build]` section entirely — `target/` is already the default output directory.

---

## 6. Removed `PathBuf` import from module but test code still needed it

**Mistake:** After `clippy` flagged `PathBuf` as unused in `storage.rs` (only `Path` was used in the public API), removed it from `use std::path::{Path, PathBuf}`. However, the `#[cfg(test)]` module's helper functions (`make_fake_pdf`, `make_non_pdf`) return `PathBuf`.

**Symptom:** Compilation error in test profile — "cannot find type `PathBuf` in this scope."

**Fix:** Added `use std::path::PathBuf;` inside the `mod tests` block so the import is scoped to test code only, keeping the non-test module clean.

---

## General Takeaways

- **Always check the actual return type** of third-party crate functions in docs or source before writing combinators.
- **Run the full `cargo fmt && cargo clippy && cargo test` cycle** after every task — catching issues early keeps fixes small.
- **When removing an import to satisfy clippy, check `#[cfg(test)]`** — test modules may depend on types that the production code doesn't use directly.
- **Write a focused test for each crate behavior assumption** (e.g., "what happens with duplicate keys?") before building logic on top of it.
