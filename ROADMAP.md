# ROADMAP

If you want to contribute you might take one of these topics and
start working on them.

## PDF or general document type content indexing

A feature that many people want appears to be search-in-document
feature, this is, the capability of searching keywords inside documents.

For this we would need a reliable way of turning PDF files or any other
format into text and being able to discriminate between trivial words
of this text and choose the most representative keywords of the text.

This in turn would be stored in some local cache and the user would
be able to search in this text like

```
papis open "text = 'neural GAN'"
```

or something like this. This would mean that the words ``neural`` and ``GAN``
should be searched also in the cache of the text-converted file.

The problems for this is that is difficult to make sure that the user
have good tools to convert into text even only for ``pdf`` and there is
no nice solution of a python library doing this.

## Implement [BASE](https://en.wikipedia.org/wiki/BASE_(search_engine)) support [X]

The great BASE search engine offers a free service for open source projects
and I have already been in contact with them, I just lack the time
to delve into their API and implement it in *clean* python.

For the moment the one interested in implementing this would have to create
a file in the spirit of

```
papis/arxiv.py
```

where a module method ``get_data`` is implemented that has a signature
similar (but not necessarily equal to)

```python
def get_data(
    query="",
    author="",
    title="",
    abstract="",
    comment="",
    journal="",
    report_number="",
    category="",
    id_list="",
    page=0,
    max_results=30
    ):
```

etc... Also the user agent of this function should be called ``papis``
as already discussed with the people from **BASE**.

## Bash and Zsh autocompletion script [X]

We have been using the package
``[argcomplete](https://github.com/kislyuk/argcomplete)``
to provide a quite rudimentary bash autocompletion.

It would be nice to have an extensible bash and zsh autocompletion
script that we can update **by hand** each time that we update
the cli. I insist it should be **by hand** in order to ensure
to better performance of the autocompletion. At least to my knowledge
``argcomplete`` has to run the program every time it spits out the
autocompletion, which in my opinion for papis is suboptimal.

Therefore is someone is skilled in bash or zsh autocompletion, she
can contribute one.

## Use [habanero](https://github.com/sckott/habanero) for ``crossref`` [X]

Right now papis is parsing crossref with a hand-made module.
However I think in order to maintain less code and profit from better
*ad-hoc* made codes we should use
[habanero](https://github.com/sckott/habanero)  to interface with
crossref since it is a very powerful library written in python.

## YouTube video explaining the main uses of `papis`.

If someone has experience with youtube, it would be nice to have a review
in youtube explaining the main uses of papis and of her workflow.

## Implement proxy to download papers. [X]

The downloaders implemented should be downloading the documents
via a normal http connection. If the users have an account at some university
where the university is paying for access to the journal, then it would
be nice that people can provide per user config a proxy that is used
to download the paper.

## Testing on Windows.

Papis should work in windows, however I am unable to test this.

## Logo.

It would be somehow nice to have a logo.

## GUI

(
There is a running project in
[here](https://github.com/PatWie/papis-webfrontend)
so before implementing a GUI yourself you might want to help out there?
)

It would be nice to have a GTK or QT based GUI, there is a branch with a gtk
GUI however I'm in principle a little bit afraid of implementing a gui
and becoming jabref. A GUI for papis should be extremely simple and
uncluttered.

People should be able to control everything by configurable
keyboard shortcuts. I do not know however if papis needs a GUI. This is
therefore a low priority for papis.

## Linux distros and macOS packages.

It would be nice to implement packages for the common linux distributions
and for Homebrew in macOS.

  - [ ] HomeBrew (MacOS)
  - [ ] Debian/Ubuntu
  - [X] Archlinux
  - [X] NixOS
  - [X] Void Linux
  - [ ] Other
