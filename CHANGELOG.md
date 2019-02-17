VERSION v0.8
============

One of the main developments for version `0.8` is to make `papis` less
dependent on `PyPi`, for which some important dependencies have been
added into the main source and is installed with it.

- Embed the following libraries in papis:
  - [`Click`](https://github.com/papis/click) version `7.0.0`
  - [`prompt_toolkit`](https://github.com/prompt-toolkit/python-prompt-toolkit)
    (solves issue #99)
  - [`colorama`](https://github.com/tartley/colorama)
  - [`filetype`](https://github.com/papis/filetype.py)
  - [`arxiv2bib`](https://github.com/papis/arxiv2bib)
  - [`python-slugify`](https://github.com/papis/python-slugify)

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
