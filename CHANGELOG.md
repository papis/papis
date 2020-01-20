VERSION v0.10
=============

- Add `--sort` and `--reverse` flags to most command line commands, together
  with the `sort-file` configuration option.
- Move `papis.utils.format_doc` to `papis.document.format_doc`
  in order to minimize circular dependencies.
- Add `--logfile` flag in order to dump log messages to a file.


## Run and `Git` command ##
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
