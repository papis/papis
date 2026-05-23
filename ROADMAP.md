# ROADMAP

If you want to contribute you might consider one of these topics and start
working on them. These are pretty big topics, so make sure to start a
discussion before embarking on them to make sure everyone is on the same page.

## PDF or general document content indexing

A feature that many people want appears to be search-in-document feature, i.e.
the capability of searching keywords inside documents, not just document metadata.

For this we would need a reliable way of turning PDF files or any other format
into text and being able to discriminate between trivial words of this text and
choose the most representative keywords of the text. This could be part of core
Papis or implemented as a separate plugin (perhaps due to some heavy dependency).

This in turn would be stored in some local cache and the user would be able to
search in this text like
```
papis open "text: 'neural GAN'"
```
or something like this. This would mean that the words ``neural`` and ``GAN``
should also be searched in the cache of the text-converted file.

The main difficulty in this implementation would be settling on a robust library
that can extract text from PDF files and index it in a convenient way. Generally
such tools are complicated to configure (mainly due to the complex PDF format)
and are rather large dependencies for a normal user. Finding a way to make all
of this work cross platform is also quite difficult, but any start in this direction
would be helpful.

## YouTube video explaining the main uses of `papis`.

If someone has experience with YouTube, it would be nice to have a review in
YouTube explaining the main uses of Papis and of its workflow.

## Improving the documentation

Papis has a very extensive set of functionality, plus many plugins and external
tools. It would be very helpful for an interested party to comb through our
existing documentation and clarify workflows, extend examples, document missing
features, etc. A good start for this can be found in the
[Discussions forum](https://github.com/papis/papis/discussions/413).

## [X] Implement proxy to download papers.

The implemented downloaders should be downloading the documents via a normal
HTTPS connection. If the users have an account at a university, where the
university is paying for access to the journal, then it would be nice to allow
users to provide a proxy that is used to download the paper.

## [X] Logo.

It would be somehow nice to have a logo.

## Linux distros and macOS packages.

It would be nice to implement packages for the common linux distributions
and for Homebrew in macOS.

  - [ ] HomeBrew (MacOS)
  - [ ] Debian/Ubuntu
  - [X] Archlinux
  - [X] NixOS
  - [X] Void Linux
  - [ ] Other
