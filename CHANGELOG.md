# VERSION 0.14.1 (March 1, 2025)

## Features

- Add a jinja2 Environment to `Jinja2Formatter`
  [#930](https://github.com/papis/papis/pull/930).

## Bug Fixes

- Do not run tests that need git when unavailable
  [#945](https://github.com/papis/papis/pull/945).
- Fix `--no-open` and `--confirm` when adding files
  [#957](https://github.com/papis/papis/pull/957).
- Fix `--file-name` being ignored when adding files
  [#964](https://github.com/papis/papis/pull/964).
- Fix piping output from the default picker
  [#969](https://github.com/papis/papis/pull/969).

# VERSION 0.14 (November 8, 2024)

## Dependency changes

- Minimum required Python version bumped to 3.8
  ([#552](https://github.com/papis/papis/pull/552)).
- Moved to `pyproject.toml` and removed `setup.py` completely. We use
  [hatchling](https://github.com/pypa/hatch/tree/master/backend) as the build
  backend.
- Removed [arxiv2bib](https://github.com/nathangrigg/arxiv2bib) in favor of
  [arxiv.py](https://github.com/lukasschwab/arxiv.py).
- Removed [tqdm](https://github.com/tqdm/tqdm) dependency (using a progress bar
  from `prompt_toolkit` instead).
- Made `chardet` an optional dependency. This is an optional dependency of
  `bs4`, `requests` and `feedparser` and should be installed if possible.
- Added [markdownify](https://github.com/matthewwithanm/python-markdownify) as
  an optional dependency for the Zenodo downloader.
- Added [platformdirs](https://github.com/platformdirs/platformdirs) dependency
  for platform-specific config locations.

## Features

### New: Improved Windows support

The support for Windows has been significantly improved in this release. On top of
a slew of fixes, there is also a build that creates a Windows executable and
installer using [PyInstaller](https://pyinstaller.org/en/stable).

These can currently be found only as artifacts under the
[Windows release workflow](https://github.com/papis/papis/actions/workflows/windows.yml).
We do urge anyone knowledgeable and interested to try them out and report any
issues, so that they can be improved before they make it into regular releases.

Huge thanks to @kiike for all the work on this!

### New: Add `cache` command ([#603](https://github.com/papis/papis/pull/603))

The `cache` command has been added in order to provide more control over the
papis cache. Accordingly, the equivalent commands `papis --cc` and
`papis --clear-cache` have been removed and can be replaced by the equivalent

```sh
papis cache clear
```

The command can now also update only specific documents using

```sh
papis cache update QUERY
```

You can learn more about the cache command in the documentation.

### New: EPUB support for the web application

Now you can read EPUB files from the comfort of the web application. The
workflow is similar to the existing one for PDFs and it uses the
[epubjs-reader](https://github.com/futurepress/epubjs-reader) library.

### New: Exporter for the Typst Hayagriva format ([#559](https://github.com/papis/papis/pull/559))

[Typst](https://github.com/typst/typst) is a new typesetting system with some
very cool features and a more modern outlook compared to LaTeX. While it
supports BibTeX, it also has its own bibliography format called Hayagriva
(a YAML file). Papis can now export directly to this format using

```
papis export --format typst QUERY
```

### New: Add `init` command ([#620](https://github.com/papis/papis/pull/620))

A new `papis init` command was added to initialize a new configuration file
and add additional libraries. The command is mainly interactive and sets some
standard default options. It can be used as

```sh
papis init /path/to/my/library
```

**Warning**: We currently use the standard Python `configparser` which does not
preserve comments. This means that updating a configuration file using `papis init`
will remove any comments and possibly reorder some options.

### New: Add `tag` command ([#648](https://github.com/papis/papis/pull/648))

A new `papis tag` command was added to handle adding and removing tags
(or keywords) for a document. For example, to add a few tags to a set of
documents

```
papis tag --add cool-project --add from-steve --all QUERY
```

or change a tag for a mislabeled document

```
papis tag --remove biology --add neuroscience QUERY
```

For more examples see the documentation.

**Warning**: The `tag` command expects that the tags are a list, not a single
string with a separator. You can quickly transform your tags into a list using
`papis doctor` e.g.

```sh
papis \
    --set doctor-key-type-keys '["tags:list"]' \
    --set doctor-key-type-separator ' ' \
    doctor --fix --all --explain -t key-type QUERY
```

where you may need to change the separator to match your choice.

### Major: Expand `update` command ([#681](https://github.com/papis/papis/pull/681))

The update command got some major improvements this release. It now allows much
more fine-grained modifications of a document without requiring the user to open
a full editor. For example, it can now

- Append to a key using

  ```sh
  papis update --append title ' (Volume 2)' <QUERY>
  ```

- Remove items from a list using

  ```sh
  papis update --remove tags 'physics' <QUERY>
  ```

- Remove a key completely from the document

  ```sh
  papis update --drop eprinttype <QUERY>
  ```

For more examples see the documentation.

### Major: Expand `doctor` command

The `papis doctor` command has seen many additions and modifications in this
release. First, the `papis add` and `papis update` commands can now automatically
run selected fixed with the `--auto-doctor` flag
([#598](https://github.com/papis/papis/pull/598)). This makes it less likely for
ill-formatted documents to make it into the library in the first place!

Many checks for BibTeX have been added: `biblatex-type-alias`, `biblatex-key-alias`
and `biblatex-required-keys` ([#663](https://github.com/papis/papis/pull/663)).
These checks ensure that the document has all the keys required by the BibLaTeX
engine to output well-formatted entries for each document type.

Other smaller noteworthy changes:

- `key-type`: added fixers that automatically convert some types
  ([#652](https://github.com/papis/papis/pull/652)
  [#656](https://github.com/papis/papis/pull/656)).
- `keys-exist`: added fixers for `author` and `author_list`
  ([#655](https://github.com/papis/papis/pull/655))
- `duplicated-values`: new check for duplicate values inside lists
  ([#695](https://github.com/papis/papis/pull/695))
- `bibtex-type`: add fixer to automatically convert known document types
  ([#732](https://github.com/papis/papis/pull/732))
- `html-tags`: be smarter about removing JATS and MML tags in abstracts.
  ([#881](https://github.com/papis/papis/pull/881)).
- [#916](https://github.com/papis/papis/pull/916) added configuration keys with
  and `-extend` suffix to enable appending instead of overwriting existing lists.
  For example, you should use `doctor-default-checks-extend = ["html-tags"]` to
  add more default checks.

### Minor: Plugin helpers ([#680](https://github.com/papis/papis/pull/680) and [#752](https://github.com/papis/papis/pull/752))

A new module `papis.testing` was introduced to help with testing Papis-related
functionality. They allow easy setup of temporary configurations and temporary
libraries for testing purposes.

A new module `papis.sphinx_ext` was introduced to help with Papis-related
documentation. This allows defining configuration options in the Sphinx documentation
that describe their types and default values in sync with the ones used in the
code.

These have mostly been promoted to separate module so that plugins can easily
make use of the same infrastructure.

### Minor: Configuration file location ([#745](https://github.com/papis/papis/pull/745))

The location of the configuration file has been standardized using
[platformdirs](https://github.com/platformdirs/platformdirs). On Linux-y systems,
this should not make any difference, since Papis has been using the XDG
environment variables to get the proper location.

However, on other systems, especially Windows and macOS, the **location of the
configuration files will change**. Papis has implemented a simple migration, so
this should be fairly automatic.

## Other noteworthy features

- Add more BibTeX key conversions
  ([#561](https://github.com/papis/papis/pull/561)
  [#562](https://github.com/papis/papis/pull/562)).
- Allow setting refs in `papis update`
  ([#593](https://github.com/papis/papis/pull/539)).
- Add proper extensions to temporary downloaded files to better differentiate
  ([#548](https://github.com/papis/papis/pull/548)).
- Updated `Dockerfile` and added `release.Dockerfile`
  ([#597](https://github.com/papis/papis/pull/597)).
- Allow `papis.format.format` to set default values and not leak exceptions
  into document fields.
  ([#596](https://github.com/papis/papis/pull/596)).
- Added a `flake.nix` script for easier use with the nix package manager
  ([#600](https://github.com/papis/papis/pull/600)).
- Updated default `opentool` on Windows
  ([#569](https://github.com/papis/papis/pull/569)).
- `papis` command: when invoking `papis` without a subcommand the help message
  is printed. This should avoid some confusions for new users
  ([#603](https://github.com/papis/papis/pull/603)).
- Allow multiple `--doc-folder` arguments to commands that support it
  ([#635](https://github.com/papis/papis/pull/635)).
- Improve ScienceDirect abstract extraction
  ([#637](https://github.com/papis/papis/pull/637))
- Better support for `--batch` in `papis add`
  ([#630](https://github.com/papis/papis/pull/630)).
- Add `--[no-]download-files` flags to `papis add`
  ([#641](https://github.com/papis/papis/pull/641)).
- Add a downloader for ACL Anthology documents
  ([#575](https://github.com/papis/papis/pull/575))
- Expand `papis list` to list all plugins and other extensions
  ([#716](https://github.com/papis/papis/pull/716))
- Add `biblatex-software` types to our BibTeX module
  ([#719](https://github.com/papis/papis/pull/719))
- Sort tags alphabetically in `papis serve`
  ([#730](https://github.com/papis/papis/pull/730))
- Add a `--move` flag to `papis add`
  ([#740](https://github.com/papis/papis/pull/740))
- Enhance `python` formatter with some additional conversions
  ([#709](https://github.com/papis/papis/pull/709))
- Fix the `these.fr` downloader
  ([#729](https://github.com/papis/papis/pull/792)).
- Add a Zenodo downloader
  ([#770](https://github.com/papis/papis/pull/770)). This uses some of the
  fields from [biblatex-software](https://ctan.org/pkg/biblatex-software?lang=en).
- Make file and folder cleanup more configurable
  ([#803](https://github.com/papis/papis/pull/803)).
- Expand the `rename` command
  ([#810](https://github.com/papis/papis/pull/810)).
- Allow configuration for marked lines margins and make marked and unmarked
  margins span the whole document entry.
  ([#820](https://github.com/papis/papis/pull/820))
- Be smarter about automatic naming of newly added files.
  ([#831](https://github.com/papis/papis/pull/831))
- Add nicer library picker.
  ([#856](https://github.com/papis/papis/pull/856)).
- Add an `edit_notes` action to the `fzf` picker.
  ([#919](https://github.com/papis/papis/pull/919))
- Add a `browse` action + shortcut to the default pickers.
  ([#922](https://github.com/papis/papis/pull/922))

## Bug fixes

- Fixed Papis to BibTeX key conversions
  ([#555](https://github.com/papis/papis/pull/555)).
- Fix encoding of `info.yaml` files on Windows
  ([#571](https://github.com/papis/papis/pull/571)).
- Fixed quoting in some calls to external commands
  ([#580](https://github.com/papis/papis/pull/580)).
- Warn and specify how external scripts are loaded.
  ([#594](https://github.com/papis/papis/pull/594)).
- Fix manpage generation from Sphinx
  ([#609](https://github.com/papis/papis/pull/609)).
- Ensure that user provided data in `papis add` using `--set key value` is not
  overwritten by importers
  ([#616](https://github.com/papis/papis/pull/616)).
- Fix some boolean flags working in an unexpected manner
  ([#636](https://github.com/papis/papis/pull/636)).
- Fix opening multiple files in the default picker
  ([#693](https://github.com/papis/papis/pull/693))
- Do not escape verbatim BibTeX fields like `url`
  ([#739](https://github.com/papis/papis/pull/739))
- Fix loading documents with removed keys.
  ([#896](https://github.com/papis/papis/pull/896))
- Use formatter for `multiple-authors-format`.
  ([#906](https://github.com/papis/papis/pull/906))

# VERSION v0.13 (May 7, 2023)

## Features

### New: Special `papis_id` key ([#449](https://github.com/papis/papis/pull/449))

In order to make plugin writing easier we have decided to introduce a
`papis_id` key in the document's info files. This key essentially functions as
a UUID for the document. Many commands have gained support for this, e.g.

```
papis list --id query
papis open papis_id:someid
```

For more information see the documentation.

**Important**: This change requires updating the database backend. This can be
done by simply clearing the cache using `papis --cc`.

### New: `papis doctor` command ([#421](https://github.com/papis/papis/pull/421))

A new `papis doctor` command was introduced that can be used to check that
document information is correct, up to date, or is nicely linted. The command
also supports fixing incorrect information for many cases!

It can be used as

```
papis doctor --checks files --explain query
```

There are several useful checks implemented already (non-exhaustive list):

- `files`: checks that the document files actually exist in the file system.
- `keys-exist`: checks that the provided keys exist in the document.
- `bibtex-type`: checks that the document type is a valid BibTeX type.
- `refs`: checks that the document ref exists and does not contain invalid characters.

For more information see the documentation.

### New: `papis citations` command ([#451](https://github.com/papis/papis/pull/451))

A new `papis citations` command was added to handle retrieving citation
information for a document. This includes both papers cited by the document
and those which cite the document itself.

For more information see the documentation.

### New: Add DBLP support ([#489](https://github.com/papis/papis/pull/489))

Add support for the [DBLP](dblp.org/) database. The database can now be explored
using

```
papis explore dblp -q query pick
```

and documents can be imported directly using the DBLP key or URL

```
papis add --from dblp 'conf/iccg/EncarnacaoAFFGM93'
```

### Major improvements to the web application ([#424](https://github.com/papis/papis/pull/424))

The Papis web application, which can be accessed with `papis serve`, has seen
major development since the last version. It now has support for

- editing of `info.yaml` file of a document (requires `ace.js`).
- viewing document PDF files directly in the browser (requires `pdfjs`).
- viewing LaTeX in titles, abstracts and others (requires `KaTeX`).
- exporting the document to BibTeX.
- showing citations for the document.
- showing errors from `papis doctor`.
- showing a timeline for queried documents.

And many other general interface and robustness improvements.

### Other noteworthy features

- A major overhaul of the README ([#415](https://github.com/papis/papis/pull/415)).
- Consistent use of ANSI colors ([#462](https://github.com/papis/papis/pull/462)).
- Better notes handling in
  `papis update` ([#404](https://github.com/papis/papis/pull/404)),
  `papis edit` ([#391](https://github.com/papis/papis/pull/391)) and
  the Papis picker ([#319](https://github.com/papis/papis/pull/319)).
- Improvements to BiBTeX export (
  [#412](https://github.com/papis/papis/pull/412)
  [#444](https://github.com/papis/papis/pull/444)
  [#443](https://github.com/papis/papis/pull/443)
  [#468](https://github.com/papis/papis/pull/468)).
- Support [NO_COLOR](https://no-color.org/)
  ([#437](https://github.com/papis/papis/pull/437)).
- Major overhaul of the `papis config` command, which can now show defaults
  and select specific sections ([#454](https://github.com/papis/papis/pull/454)).
- Fix shell completion on `bash`, `zsh`, and `fish`
  ([#478](https://github.com/papis/papis/pull/478)).
- Update the logging format ([#465](https://github.com/papis/papis/pull/465)).
- Updated multiple downloaders to support the latest version of the website
  and for better data extraction (
  [#441](https://github.com/papis/papis/pull/441)
  [#447](https://github.com/papis/papis/pull/447)).
- Avoid downloading files on `papis add` in certain scenarios
  ([#505](https://github.com/papis/papis/pull/505)).
- Recognize `DjVu` files correctly ([#522](https://github.com/papis/papis/pull/522)).
- Add USENIX downloader ([#523](https://github.com/papis/papis/pull/523)).
- Support remote URLs in `papis addto` ([#541](https://github.com/papis/papis/pull/541)).
- Add `sort-reverse` configuration option ([#543](https://github.com/papis/papis/pull/543)).

## Bug fixes

- Properly detach processes on `papis open` ([#476](https://github.com/papis/papis/pull/476)).
- Fix link extraction in `crossref` ([#480](https://github.com/papis/papis/pull/480)).
- Do not generate refs in downloaders ([#483](https://github.com/papis/papis/pull/483)).
- Fix empty config file handling ([#497](https://github.com/papis/papis/pull/497)).
- Fix database query for `jinja2` ([#499](https://github.com/papis/papis/pull/499)).
- Fix crash on trying to add a duplicate document ([#510](https://github.com/papis/papis/pull/510)).
- Fix many typos ([#540](https://github.com/papis/papis/pull/540)).

# VERSION v0.12 (May 23, 2022)

Many issues were resolved and new (and old) contributors
made the following changes possible.

## Add hook infrastructure

A basic hook infrastructure has been added to be able to
use emacs-like hooks for some commands.

## Add `additional` keyword for the formatter plugin system

## `papis bibtex`

- Add `import` command to import bibtex files as papis documents
  into the library.
- Add `filter-cited`.

## `papis exec`

- Add command `exec` to run python scripts in the environment of the
  papis executable.

## papis picker

- You can now pick several elements with the key binding `c-t`
- Add support for fzf picker,
  check out the [documentation](https://papis.readthedocs.io/en/latest/configuration.html#fzf-integration).

## `papis merge`

- Add the command `papis merge` to merge documents in pairs.

## `papis browse`

- Add `-n` and `--print` to just print the url to be opened.

## Downloaders

- Add an `acm` downloader
- Add an `Project Euclid` downloader

## Notes

Now you can remove notes files with `papis rm --notes`
or have templates for the notes.
Check out the
[notes-template variable](https://papis.readthedocs.io/en/latest/configuration.html#config-settings-notes-template).

## Web application `papis serve`

- The new, simple and experimental web application is available
  through the `papis serve` command.
  Feel free to make suggestions.

## MacOS

- disable multiprocessing by default on mac due to lack of performance and source
  of strange behaviour.

## Community

- usage of github discussions and #papis channel on libera.

# VERSION v0.11 (October 17, 2020)

## `papis explore`

- Add `add` command to simply add documents retrieved.

## `papis.export`

- Add the key `_papis_local_folder` so that third-party apps
  can get the documents' paths without having to go again through papis.

## `papis bibtex`

- Add `unique` command to be able to merge different bib files
  and filter out repetitions.
- Add `doctor` to check for fields in a bibfile.
- Add `iscited` to check which bib items are cited in a text file.

## Add Format plugin

- Sébastien Popoff has added a format plugin architecture, so now `jinja2`
  is available again as a plugin.

## Bibtex

- Improve the reference building routine.
- Change the default `ref-format` to
  ```
  "{doc[title]:.15} {doc[author]:.6} {doc[year]}",
  ```
- The default ref if no reference could be built will not be
  using the folder name as before, but using the values in the `info.yaml`
  limited to 30 characters.

## `papis add`

- Create a reference at the time of adding if no reference exists.

## `papis browse`

- Add more documentation.
- Add an `ads` handler to jump into the `ads` website of the paper
  using a doi.

# VERSION v0.10 (May 2, 2020)

- Fix several bugs.
- Typecheck the whole codebase
  and drop support for python versions up to 3.4, the latter version included.
- Add `--sort` and `--reverse` flags to most command line commands, together
  with the `sort-file` configuration option.
  see [doc](https://papis.readthedocs.io/en/latest/configuration.html#config-settings-sort-field).
- Add `time-stamps` in order to sort chronologically documents
  see [doc](https://papis.readthedocs.io/en/latest/configuration.html#config-settings-time-stamp).
- Add `--doc-folder` to most command line commands for better bash-scripting
  capabilities.
- Add `--logfile` flag in order to dump log messages to a file.
- Move `papis.utils.format_doc` to `papis.document.format_doc`
  in order to minimize circular dependencies.
- Add a `--profile` flag to profile the papis run.
- Define a new API for general pickers. (TBD)
- Add a citeseerx downloader.

## `papis add`

- Add an experimental importer selector when smart matching inputs.
  See [here](https://asciinema.org/a/i2kXyZMNaT8n7YRz7DcVIfqm5).

## `papis bibtex`

- Add `papis bibtex browse`.

## `Run` and `Git` command

- Add `--pick`, `--doc-folder`, `--all` and `--sort`
  flags so that we can choose a document to run the shell or git command
  in that folder or in all folders matching a given query introduced by
  `--pick`.

# VERSION v0.9 (October 21, 2019)

## Plugin architecture

A new plugin architecture is in place.
For more information please refer to
[the documentation](https://papis.readthedocs.io/en/latest/plugin.html)

## Git interface

Now some usual commands have a `--git` flag that lets the command work
alongside git. For instance if the `--git` flag is passed to `papis-edit`,
it will add and commit the `info.yaml` file automatically. The same applies
to `papis-add`, `papis-addto`, `papis-update` and `papis-rm`.

You can activate by default the `--git` flag using the `use-git` configuration
option.
**For devs**: The main functions to implement this interface are found in the
papis module `papis.git`.

## `papis add`

- The configuration settings `file-name` and `folder-name` are now

  ```
  add-file-name
  add-folder-name
  ```

  so that they become more readable and understandable.
  Also the flag `--name` is now `--folder-name`.

- The flag `--commit` now has the name `--git`.

- The flag `--dir` now has the more descriptive name `--subfolder`.

- The flag `--no-document` has been finally removed.

- The most notable update is that the `papis` commands are now able to guess a `doi`
  or `arxiv` id from a pdf that is being added, so the following could work

  ```
  papis add --confirm arxiv-paper.pdf
  ```

  or

  ```
  papis add --confirm some-random-paper.pdf
  ```

  with the `--confirm` flag it will ask if we want to use the `doi` or `arxivid`
  retrieved.

- We can query `crossref` with `--from-crossref` in order to get information
  and add a paper.

## `papis export`

- The configuration settings `export-text-format` has been removed along with
  the export --text command. Papis now support plugins so you should write your
  own instead.
- The flags --bibtex/--json/--yaml of the `export` command have been replaced
  by `export --format=bibtex/json/yaml`
- The flag `--file` has been removed, if you want to export the related files
  then just either export the folder or write a small script for it.

## `papis explore`

- Change the flags for `papis explore export` to match the `papis export`
  command.

## `papis list`

- Add `-n, --notes` flags to list notes.
- Remove the `--pick` flag and add the `--all` flag to be consistent with the
  behaviour of other commands.
- Remove the query argument in the `run` function for consistency with other
  commands.

## `papis browse`

- Add `--all` flag, improve tests and log.

## Databases

- The default `papis` database is now caching the document objects instead
  of only the paths, which means that no yaml parsing is necessary every
  time, which makes it around `10x` faster than in version `v0.8`.
  For a library of 1200 documents, the speed of the `papis` database backend
  is comparable with the `whoosh` backend.
- The query language for the default `papis` database has changed, now
  the setter character is `:` instead of `=` to better conform with other
  common database engines like `whoosh` or `xapian`. For instance, before
  ```
  papis open 'author=einstein year=1905'
  ```
  and now it will be
  ```
  papis open 'author:einstein year:1905'
  ```
- Libraries can have multiple directories defined.

## Configuration

- A `~/.config/papis/config.py` python file has been added which is
  sourced after the `~/.config/papis/config` file has been processed.
  This should enable some users to have more granularity in the customization.

## Downloaders

- Some downloaders have been improved and a `fallback` downloader has
  been added. Now you will be able to retrieve information
  from many more websites by by virtue of the metadata of html websites.

# VERSION v0.8.1 (February 27, 2019)

- Change default colors for `header_formater`.
- Update `prompt_toolkit` version to `2.0.5`.

# VERSION v0.8 (February 26, 2019)

One of the main developments for version `0.8` is to make `papis` less
dependent on `PyPi`, for which some important dependencies have been
added into the main source and is installed with it.

- Redesign of the picker and `tui`.

- Add `text_area` widget for duplication warnings and `papis rm`

- Add color to the logs and potentially throughout the project.

- Add rudimentary [BASE](https://www.base-search.net/about/en/) parser
  and include it in `papis explore` and `papis update`.

- Update Hyperlink DOIs to preferred resolver (issue #136)

- Add click based shell completion for `bash` and `zsh`.
  Consult the [docs](https://papis.readthedocs.io/en/latest/shell_completion.html).

- Add bibtex tests

- Update export format in bibtex

- Fix help string in commands

- `papis export -o` now appends and does not overwrite

- Fix existing paths in command `addto`

- Add `@papis.cli.bypass` decorator for scripts

- Remove `xeditor` config parameter

- Add external picker in api

- Erase all guis from Papis main repository, they should be used in external
  scripts or projects, [docs](https://papis.readthedocs.io/en/latest/gui.html).

- Fix downloader testing framework.

- Add downloader for:

  - `frontiersin.org`
  - `hal.fr`
