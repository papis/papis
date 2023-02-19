VERSION v0.13
=============

## Features

### New: Special `papis_id` key ([#449](https://github.com/papis/papis/pull/449))

In order to make plugin writing easier we have decided to introduce a
`papis_id` key in the document's info files. This key essentially functions as
a UUID for the document. Many commands have gained support for this, e.g.

    papis list --id query
    papis open papis_id:someid

For more information see the documentation.

**Important**: This change requires updating the database backend. This can be
done by simply clearing the cache using `papis --cc`.

### New: `papis doctor` command ([#421](https://github.com/papis/papis/pull/421))

A new `papis doctor` command was introduced that can be used to check that
document information is correct, up to date, or is nicely linted. The command
also supports fixing incorrect information for many cases!

It can be used as

    papis doctor --checks files --explain query

There are several useful checks implemented already (non-exhaustive list):

* `files`: checks that the document files actually exist in the file system.
* `keys-exist`: checks that the provided keys exist in the document.
* `bibtex-type`: checks that the document type is a valid BibTeX type.
* `refs`: checks that the document ref exists and does not contain invalid characters.

For more information see the documentation.

### New: `papis citations` command ([#451](https://github.com/papis/papis/pull/451))

A new `papis citations` command was added to handle retrieving citation
information for a document. This includes both papers cited by the document
and those which cite the document itself.

For more information see the documentation.


### New: Add DBLP support ([#489](https://github.com/papis/papis/pull/489))

Add support for the [DBLP](dblp.org/) database. The database can now be explored
using

    papis explore dblp -q query pick

and documents can be imported directly using the DBLP key or URL

    papis add --from dblp 'conf/iccg/EncarnacaoAFFGM93'

### Major improvements to the web application ([#424](https://github.com/papis/papis/pull/424))

The Papis web application, which can be accessed with `papis serve`, has seen
major development since the last version. It now has support for

* editing of `info.yaml` file of a document (requires `ace.js`).
* viewing document PDF files directly in the browser (requires `pdfjs`).
* viewing LaTeX in titles, abstracts and others (requires `KaTeX`).
* exporting the document to BibTeX.
* showing citations for the document.
* showing errors from `papis doctor`.
* showing a timeline for queried documents.

And many other general interface and robustness improvements.

### Other noteworthy features

* A major overhaul of the README ([#415](https://github.com/papis/papis/pull/415)).
* Consistent use of ANSI colors ([#462](https://github.com/papis/papis/pull/462)).
* Better notes handling in
  `papis update` ([#404](https://github.com/papis/papis/pull/404)),
  `papis edit` ([#391](https://github.com/papis/papis/pull/391)) and
  the papis picker ([#319](https://github.com/papis/papis/pull/319)).
* Improvements to BiBTeX export (
  [#412](https://github.com/papis/papis/pull/412)
  [#444](https://github.com/papis/papis/pull/444)
  [#443](https://github.com/papis/papis/pull/443)
  [#468](https://github.com/papis/papis/pull/468)).
* Support [NO_COLOR](https://no-color.org/)
  ([#437](https://github.com/papis/papis/pull/437)).
* Major overhaul of the `papis config` command, which can now show defaults
  and select specific sections ([#454](https://github.com/papis/papis/pull/454)).
* Fix shell completion on `bash`, `zsh`, and `fish`
  ([#478](https://github.com/papis/papis/pull/478)).
* Update the logging format ([#465](https://github.com/papis/papis/pull/465)).
* Updated multiple downloaders to support the latest version of the website
  and for better data extraction (
  [#441](https://github.com/papis/papis/pull/441)
  [#447](https://github.com/papis/papis/pull/447)).
* Avoid downloading files on `papis add` in certain scenarios
  ([#505](https://github.com/papis/papis/pull/505)).
* Recognize `DjVu` files correctly ([#522](https://github.com/papis/papis/pull/522)).
* Add USENIX downloader ([#523](https://github.com/papis/papis/pull/523)).
* Support remote URLs in `papis addto` ([#541](https://github.com/papis/papis/pull/541)).
* Add `sort-reverse` configuration option ([#543](https://github.com/papis/papis/pull/543)).

## Bug fixes

* Properly detach processes on `papis open` ([#476](https://github.com/papis/papis/pull/476)).
* Fix link extraction in `crossref` ([#480](https://github.com/papis/papis/pull/480)).
* Do not generate refs in downloaders ([#483](https://github.com/papis/papis/pull/483)).
* Fix empty config file handling ([#497](https://github.com/papis/papis/pull/497)).
* Fix database query for `jinja2` ([#499](https://github.com/papis/papis/pull/499)).
* Fix crash on trying to add a duplicate document ([#510](https://github.com/papis/papis/pull/510)).
* Fix many typos ([#540](https://github.com/papis/papis/pull/540)).

VERSION v0.12
=============

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

VERSION v0.11
=============

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


VERSION v0.10
=============

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



VERSION v0.9
============

## Plugin architecture ##

A new plugin architecture is in place.
For more information please refer to
[the documentation](https://papis.readthedocs.io/en/latest/plugin.html)

## Git interface ##

Now some usual commands have a `--git` flag that lets the command work
alongside git. For instance if the `--git` flag is passed to `papis-edit`,
it will add and commit the `info.yaml` file automatically. The same applies
to `papis-add`, `papis-addto`, `papis-update` and `papis-rm`.

You can activate by default the `--git` flag using the `use-git` configuration
option.
**For devs**: The main functions to implement this interface are found in the
papis module `papis.git`.

## `papis add` ##

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
- The most notable update is that papis is now able to guess a `doi`
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

## `papis export` ##

- The configuration settings `export-text-format` has been removed along with
  the export --text command. papis now support plugins so you should write your
  own instead.
- The flags --bibtex/--json/--yaml of the `export` command have been replaced
  by `export --format=bibtex/json/yaml`
- The flag `--file` has been removed, if you want to export the related files
  then just either export the folder or write a small script for it.

## `papis explore` ##

- Change the flags for `papis explore export` to match the `papis export`
  command.

## `papis list` ##

- Add `-n, --notes` flags to list notes.
- Remove the `--pick` flag and add the `--all` flag to be consistent with the
  behaviour of other commands.
- Remove the query argument in the `run` function for consistency with other
  commands.

## `papis browse` ##

- Add `--all` flag, improve tests and log.

## Databases ##


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

## Configuration ##

- A `~/.config/papis/config.py` python file has been added which is
  sourced after the `~/.config/papis/config` file has been processed.
  This should enable some users to have more granularity in the customization.

## Downloaders ##

- Some downloaders have been improved and a `fallback` downloader has
  been added. Now you will be able to retrieve information
  from many more websites by by virtue of the metadata of html websites.

VERSION v0.8.1
==============

- Change default colors for `header_formater`.
- Update `prompt_toolkit` version to `2.0.5`.

VERSION v0.8
============

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

- Erase all guis from papis main repository, they should be used in external
  scripts or projects, [docs](https://papis.readthedocs.io/en/latest/gui.html).

- Fix downloader testing framework.
- Add downloader for:
  - `frontiersin.org`
  - `hal.fr`
