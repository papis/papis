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
papis open "text: 'neural GAN'"
```

or something like this. This would mean that the words ``neural`` and ``GAN``
should be searched also in the cache of the text-converted file.

The problems for this is that is difficult to make sure that the user
have good tools to convert into text even only for ``pdf`` and there is
no nice solution of a python library doing this.

## YouTube video explaining the main uses of `papis`.

If someone has experience with youtube, it would be nice to have a review
in youtube explaining the main uses of papis and of her workflow.

## Implement proxy to download papers. [X]

The downloaders implemented should be downloading the documents
via a normal http connection. If the users have an account at some university
where the university is paying for access to the journal, then it would
be nice that people can provide per user config a proxy that is used
to download the paper.

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
