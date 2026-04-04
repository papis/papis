//! papis-rs: A minimal single-user, single-library reference manager CLI.
//!
//! This binary provides five MVP subcommands:
//! - `init`       – create a new library directory with SQLite + storage
//! - `import-bib` – parse a .bib file and store entries in SQLite
//! - `add-pdf`    – attach a PDF to an existing entry
//! - `list`       – list all entries in the library
//! - `show`       – show one entry's metadata and attached files

mod bib;
mod cli;
mod db;
mod model;
mod storage;

use clap::{Parser, Subcommand};
use std::path::PathBuf;

// ---------------------------------------------------------------------------
// Top-level CLI definition (clap derive)
// ---------------------------------------------------------------------------

/// papis-rs – a minimal reference-library manager.
#[derive(Parser)]
#[command(name = "papis-rs", version, about)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

/// The five MVP subcommands.
///
/// Every command requires `--library <path>` so library data always lives
/// outside the repository (no hidden state or config discovery in the MVP).
#[derive(Subcommand)]
enum Commands {
    /// Initialize a new library (creates SQLite DB + storage directory).
    Init {
        /// Path to the library root directory.
        #[arg(long)]
        library: PathBuf,
    },

    /// Import entries from a BibTeX `.bib` file into the library.
    ImportBib {
        /// Path to the library root directory.
        #[arg(long)]
        library: PathBuf,
        /// Path to the `.bib` file to import.
        bib_file: PathBuf,
    },

    /// Attach a PDF file to an existing entry (looked up by BibTeX key).
    AddPdf {
        /// Path to the library root directory.
        #[arg(long)]
        library: PathBuf,
        /// The BibTeX key of the target entry.
        bibtex_key: String,
        /// Path to the PDF file to attach.
        pdf_file: PathBuf,
    },

    /// List all entries stored in the library.
    List {
        /// Path to the library root directory.
        #[arg(long)]
        library: PathBuf,
    },

    /// Show detailed metadata for one entry (looked up by BibTeX key).
    Show {
        /// Path to the library root directory.
        #[arg(long)]
        library: PathBuf,
        /// The BibTeX key of the entry to display.
        bibtex_key: String,
    },
}

// ---------------------------------------------------------------------------
// Entry point – parse args and dispatch to the matching command handler.
// ---------------------------------------------------------------------------

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Init { library } => cli::run_init(&library),
        Commands::ImportBib { library, bib_file } => cli::run_import_bib(&library, &bib_file),
        Commands::AddPdf {
            library,
            bibtex_key,
            pdf_file,
        } => cli::run_add_pdf(&library, &bibtex_key, &pdf_file),
        Commands::List { library } => cli::run_list(&library),
        Commands::Show {
            library,
            bibtex_key,
        } => cli::run_show(&library, &bibtex_key),
    }
}
