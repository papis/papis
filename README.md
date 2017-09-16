
# Papis

[![Build Status](https://travis-ci.org/alejandrogallo/papis.svg?branch=master)](https://travis-ci.org/alejandrogallo/papis)

<a href='http://papis.readthedocs.io/en/latest/?badge=latest'>
    <img src='https://readthedocs.org/projects/papis/badge/?version=latest' alt='Documentation Status' />
</a>

<a href="https://badge.fury.io/py/papis">
  <img src="https://badge.fury.io/py/papis.svg" alt="PyPI version" height="18">
</a>

## Description

Papis is a powerful and highly extensible command-line based document and
bibliography manager.

Take a look at the [documentation](http://papis.readthedocs.io/en/latest/)!

## Super quick start

Install papis with pip3
```
sudo pip3 install papis
```

Let us download a couple of documents
```
wget http://www.gnu.org/s/libc/manual/pdf/libc.pdf
wget https://gcc.gnu.org/onlinedocs/cpp.pdf
```

Now add them to the (defaultly created) library
```
papis add libc.pdf --author "Sandra Loosemore" --title "GNU C reference manual" --confirm
papis add cpp.pdf --author "R. Stallman et al." --title "The C Preprocessor" --confirm
```

Now open one for example
```
papis open
```

[![asciicast](https://asciinema.org/a/HVMFsvBE9blDpzYYg9jsSEaO0.png)](https://asciinema.org/a/HVMFsvBE9blDpzYYg9jsSEaO0)
Or export them to bibtex
```
papis export --bibtex --all > mylib.bib
```

[![asciicast](https://asciinema.org/a/LqGxoYp0RV78eg4hQBdhKQjst.png)](https://asciinema.org/a/LqGxoYp0RV78eg4hQBdhKQjst)

AND MUCH, MUCH MORE!

## Help Wanted

*Papis* is looking for active developers to help improve the code.

## TODO

- [ ] Implement a mini query language in order to filter by field the searches,
  for example:
  ```
  papis open "author=stein year=192 ueber die "
  ```
  so that it matches all papers with a regex match for `stein`, then also where
  the year matches `192` (i.e., 1920, 1921...) and then also it matches
  `ueber die` using the default `match-format` configuration variable.
  This can be done by updating the function `papis.utils.match_document`.
- [X] Match search strings to documents using multiple cores
  through the standard `multiprocess` module.
- [X] Make sure that `setup.py` installs the `python-rofi` module from
  `https://github.com/alejandrogallo/python-rofi` and not from the original
  website.
- [X] Bibitem support for exporting references in the export command.
    (**Done** through the ``--template`` option of list)
- [ ] Youtube video explaining the main uses of `papis`.
- [ ] Implement proxy to donwload papers.
- [ ] Debian package.
- [ ] Testing on Windows.
- [ ] Logo.
- [ ] Gtk or Qt based GUI.

