
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
wget http://www.ams.org/notices/201304/rnoti-p434.pdf 
```

Now add them to the (defaultly created) library
```
papis add libc.pdf --author "Sandra Loosemore" --title "GNU C reference manual" --confirm
# Get paper information automatically via de DOI
papis add --from-doi 10.1090/noti963 rnoti-p434.pdf 
```

Now open one for example
```
papis open
```


[![asciicast](https://asciinema.org/a/oEHU9oPlGrKPOQzGMxvqkh5Fe.png)](https://asciinema.org/a/oEHU9oPlGrKPOQzGMxvqkh5Fe)
Or edit them and export them to bibtex

```
papis edit
papis export --all --bibtex > mylib.bib
```

[![asciicast](https://asciinema.org/a/QrUntd87K97hoKowxkAb4AYZ0.png)](https://asciinema.org/a/QrUntd87K97hoKowxkAb4AYZ0)

find help messages in all commands:
```
papis -h
papis add -h
```

[![asciicast](https://asciinema.org/a/48Dv1rfX44yjJD6Sbc71gpXGr.png)](https://asciinema.org/a/48Dv1rfX44yjJD6Sbc71gpXGr)
AND MUCH, MUCH MORE!

## Main features

  - Synchronizing of documents: put your documents in some folder and
    synchronize it using the tools you love: git, dropbox, rsync, OwnCloud,
    Google Drive ... whatever.
  - Share libraries with colleagues without forcing them to open an account,
    nowhere, never.
  - Download directly paper information from *DOI* number via *Crossref*.
  - (optional) **scihub** support, use the example papis script
    `examples/scripts/papis-scihub` to download papers from scihub and add them
    to your library with all the relevant information, in a matter of seconds,
    also you can check the documentation
     [here](http://papis.readthedocs.io/en/latest/scihub.html).
  - Import from Zotero and other managers using the script in
    `examples/scripts/papis-zotero`
    ([doc](http://papis.readthedocs.io/en/latest/importing.html)).
  - Create custom scripts to help you achieve great tasks easily
    ([doc](http://papis.readthedocs.io/en/latest/scripting.html)).
  - Export documents into many formats (bibtex, yaml..)
  - Command-line granularity, all the power of a library at the tip of your
    fingers.

## TODO

- [X] Implement a mini query language in order to filter by field the searches,
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
- [ ] Testing on Windows.
- [ ] Logo.
- [ ] Gtk or Qt based GUI.

