# -*- coding: utf-8 -*-
r"""

This command helps to interact with `bib` files in your LaTeX projects.

Examples
^^^^^^^^

I use it for opening some papers for instance

::

    papis bibtex read new_papers.bib open

or to add papers to the bib

::

    papis bibtex          \
      read new_papers.bib \ # Read bib file
      add einstein        \ # Pick a doc with query 'einstein' from library
      add heisenberg      \ # Pick a doc with query 'heisenberg' from library
      save new_papers.bib   # Save in new_papers.bib

or if I update some information in my papis ``yaml`` files then I can do

::

    papis bibtex          \
      read new_papers.bib \ # Read bib file
      update -f           \ # Update what has been read from papis library
      save new_papers.bib   # save everything to new_papers.bib, overwriting

Local configuration file
^^^^^^^^^^^^^^^^^^^^^^^^

If you are working in a local folder where you have
a bib file called ``main.bib``, you'll grow sick and tired
of writing always ``read main.bib`` and  ``save main.bib``, so you can
write a local configuration file ``.papis.config`` for ``papis bibtex``
to read and write automatically

::

    [bibtex]
    default-read-bibfile = main.bib
    default-save-bibfile = main.bib
    auto-read = True

with this setup, you can just do

::

    papis bibtex add einstein save

Check references quality
^^^^^^^^^^^^^^^^^^^^^^^^

When you're collaborating with someone, you might come across malformed
or incomplete references. Most journals want to have all the ``doi``s
and urls available. You can automate this diagnostic with

For this you kan use the command ``doctor``

::

    papis bibtex read mybib.bib doctor

Mostly I want to have only the references in my project's bib file
that are actually cited in the latex file, you can check
which references are not cited in the tex files by doing


::

    papis bibtex iscited -f main.tex -f chapter-2.tex

and you can then filter them out using the command ``filter-cited``.

To monitor the health of the bib project's file, I mostly have a
target in the project's ``Makefile`` like

.. code:: make

    .PHONY: check-bib
    check-bib:
        papis bibtex iscited -f main.tex doctor

it does not solve all problems under the sun, but it is really better than no
check!



Vim integration
^^^^^^^^^^^^^^^

Right now, you can easily use it from vim with these simple lines

.. code:: vimscript

    function! PapisBibtexRef()
      let l:temp = tempname()
      echom l:temp
      silent exec "!papis bibtex ref -o ".l:temp
      let l:olda = @a
      let @a = join(readfile(l:temp), ',')
      normal! "ap
      redraw!
      let @a = l:olda
    endfunction

    command! -nargs=0 BibRef call PapisBibtexRef()
    command! -nargs=0 BibOpen exec "!papis bibtex open"

And use like such: |asciicast|

.. |asciicast| image:: https://asciinema.org/a/8KbLQJSVYVYNXHVF3wgcxx5Cp.svg
   :target: https://asciinema.org/a/8KbLQJSVYVYNXHVF3wgcxx5Cp

Cli
^^^
.. click:: papis.commands.bibtex:cli
    :prog: papis bibtex

"""
import os
import re
import click
import logging
from typing import List, Optional

import papis.api
import papis.cli
import papis.config as config
import papis.utils
import papis.tui.utils
import papis.commands.explore as explore
import papis.commands.add
import papis.commands.open
import papis.commands.edit
import papis.commands.browse
import papis.commands.export
import papis.bibtex


logger = logging.getLogger('papis:bibtex')


config.register_default_settings({'bibtex': {
    'default-read-bibfile': '',
    'auto-read': '',
    'default-save-bibfile': ''
}})

explorer_mgr = explore.get_explorer_mgr()


@click.group("bibtex", cls=papis.cli.AliasedGroup, chain=True)
@click.help_option('-h', '--help')
@click.option('--noar', '--no-auto-read', 'no_auto_read',
              default=False,
              is_flag=True,
              help="Do not auto read even if the configuration file says it")
@click.pass_context
def cli(ctx: click.Context, no_auto_read: bool) -> None:
    """A papis script to interact with bibtex files"""
    global explorer_mgr
    ctx.obj = {'documents': []}

    if no_auto_read:
        logger.info("Setting 'auto-read' to False")
        config.set('auto-read', 'False', section='bibtex')

    bibfile = config.get('default-read-bibfile', section='bibtex')
    if (bool(config.getboolean('auto-read', section='bibtex'))
            and bibfile
            and os.path.exists(bibfile)):
        logger.info("Auto-reading '%s'", bibfile)
        explorer_mgr['bibtex'].plugin.callback(bibfile)


cli.add_command(explorer_mgr['bibtex'].plugin, 'read')


@cli.command('add')
@papis.cli.query_option()
@click.help_option('-h', '--help')
@papis.cli.all_option()
@click.pass_context
def _add(ctx: click.Context, query: str, _all: bool) -> None:
    """Add a reference to the bibtex file"""
    docs = papis.api.get_documents_in_lib(search=query)
    if not _all:
        docs = list(papis.api.pick_doc(docs))
    ctx.obj['documents'].extend(docs)


@cli.command('update')
@click.help_option('-h', '--help')
@papis.cli.all_option()
@click.option('--from', '-f', 'fromdb',
              show_default=True,
              help='Update the document from the library',
              default=False, is_flag=True)
@click.option('-t', '--to',
              help='Update the library document from retrieved document',
              show_default=True,
              default=False, is_flag=True)
@click.option('-k', '--keys',
              help='Update only given keys (can be given multiple times)',
              type=str,
              multiple=True)
@click.pass_context
def _update(ctx: click.Context, _all: bool,
            fromdb: bool, to: bool, keys: List[str]) -> None:
    """Update documents from and to the library"""
    docs = click.get_current_context().obj['documents']
    picked_doc = None
    if not _all:
        picked_docs = papis.api.pick_doc(docs)
        if picked_docs is None or picked_docs[0] is None:
            return
        picked_doc = picked_docs[0]
    for j, doc in enumerate(docs):
        if picked_doc and doc["ref"] != picked_doc["ref"]:
            continue
        try:
            libdoc = papis.utils.locate_document_in_lib(doc)
        except IndexError as e:
            logger.info(
                '{c.Fore.YELLOW}%s:'
                '\n\t{c.Back.RED}%-80.80s{c.Style.RESET_ALL}',
                e, papis.document.describe(doc))
        else:
            if fromdb:
                logger.info(
                    'Updating \n\t{c.Fore.GREEN}'
                    '{c.Back.BLACK}%-80.80s{c.Style.RESET_ALL}',
                    papis.document.describe(doc))
                if keys:
                    docs[j].update(
                        {k: libdoc.get(k) for k in keys if libdoc.has(k)})
                else:
                    docs[j] = libdoc
    click.get_current_context().obj['documents'] = docs


@cli.command('open')
@click.help_option('-h', '--help')
@click.pass_context
def _open(ctx: click.Context) -> None:
    """Open a document in the documents list"""
    docs = ctx.obj['documents']
    docs = papis.api.pick_doc(docs)
    if not docs:
        return
    doc = papis.utils.locate_document_in_lib(docs[0])
    papis.commands.open.run(doc)


@cli.command('edit')
@click.help_option('-h', '--help')
@click.option('-l', '--lib',
              show_default=True,
              help='Edit document in papis library',
              default=False, is_flag=True)
@click.pass_context
def _edit(ctx: click.Context, lib: bool) -> None:
    """edit a document in the documents list"""
    docs = ctx.obj['documents']
    docs = papis.api.pick_doc(docs)
    if not docs:
        return
    doc = papis.utils.locate_document_in_lib(docs[0])
    papis.commands.edit.run(doc)


@cli.command('browse')
@click.help_option('-h', '--help')
@click.option('-k', '--key', default=None, help="doi, url, ...")
@click.pass_context
def _browse(ctx: click.Context, key: Optional[str]) -> None:
    """browse a document in the documents list"""
    docs = papis.api.pick_doc(ctx.obj['documents'])
    if key:
        config.set("browse-key", key)
    if not docs:
        return
    for d in docs:
        papis.commands.browse.run(d)


@cli.command('rm')
@click.help_option('-h', '--help')
@click.pass_context
def _rm(ctx: click.Context) -> None:
    """Remove a document from the documents list"""
    print('Sorry, TODO...')


@cli.command('ref')
@click.help_option('-h', '--help')
@click.option('-o', '--out', help='Output ref to a file', default=None)
@click.pass_context
def _ref(ctx: click.Context, out: Optional[str]) -> None:
    """Print the reference for a document"""
    docs = ctx.obj['documents']
    docs = papis.api.pick_doc(docs)
    if not docs:
        return
    ref = docs[0]["ref"]
    if out:
        with open(out, 'w+') as fd:
            fd.write(ref)
    else:
        print(ref)


@cli.command('save')
@click.help_option('-h', '--help')
@click.argument(
    'bibfile',
    default=lambda: config.get('default-save-bibfile', section='bibtex'),
    required=True, type=click.Path())
@click.option('-f', '--force', default=False, is_flag=True)
@click.pass_context
def _save(ctx: click.Context, bibfile: str, force: bool) -> None:
    """Save the documents imported in bibtex format"""
    docs = ctx.obj['documents']
    if not force:
        c = papis.tui.utils.confirm('Are you sure you want to save?')
        if not c:
            print('Not saving..')
            return
    with open(bibfile, 'w+') as fd:
        logger.info("Saving %d documents in '%s'", len(docs), bibfile)
        fd.write(papis.commands.export.run(docs, to_format='bibtex'))


@cli.command('sort')
@click.help_option('-h', '--help')
@click.option('-k', '--key',
              help="Field to order it",
              default=None,
              type=str,
              required=True)
@click.option('-r', '--reverse',
              help="Reverse the order",
              default=False,
              is_flag=True)
@click.pass_context
def _sort(ctx: click.Context, key: Optional[str], reverse: bool) -> None:
    """Sort documents"""
    docs = ctx.obj['documents']
    ctx.obj['documents'] = list(sorted(docs,
                                       key=lambda d: str(d[key]),
                                       reverse=reverse))


@cli.command('unique')
@click.help_option('-h', '--help')
@click.option('-k', '--key',
              help="Field to test for uniqueness, default is ref",
              default="ref",
              type=str)
@click.option('-o',
              help="Output the discarded documents to a file",
              default=None,
              type=str)
@click.pass_context
def _unique(ctx: click.Context, key: str, o: Optional[str]) -> None:
    """Remove repetitions"""
    docs = ctx.obj['documents']
    unique_docs = []
    duplis_docs = []

    while True:
        if not len(docs):
            break
        doc = docs.pop(0)
        unique_docs.append(doc)
        indices = []
        for i, bottle in enumerate(docs):
            if doc.get(key) == bottle.get(key):
                indices.append(i)
                duplis_docs.append(bottle)
                logger.info(
                        '%d repeated %s -> %s',
                        len(duplis_docs), key, doc.get(key))
        docs = [d for (i, d) in enumerate(docs) if i not in indices]

    logger.info("Unique   : %d", len(unique_docs))
    logger.info("Discarded: %d", len(duplis_docs))

    ctx.obj['documents'] = unique_docs
    if o:
        with open(o, 'w+') as f:
            logger.info("Saving %d documents in '%s'", len(duplis_docs), o)
            f.write(papis.commands.export.run(duplis_docs, to_format='bibtex'))


@cli.command('doctor')
@click.help_option('-h', '--help')
@click.option('-k', '--key',
              help="Field to test for uniqueness, default is ref",
              multiple=True,
              default=("doi", "url", "year", "title", "author"),
              type=str)
@click.pass_context
def _doctor(ctx: click.Context, key: List[str]) -> None:
    """
    Check bibfile for correctness, missing keys etc.
        e.g. papis bibtex doctor -k title -k url -k doi

    """
    logger.info("Checking for existence of keys %s", ", ".join(key))

    failed = [(d, keys) for d, keys in [(d, [k for k in key if not d.has(k)])
                                        for d in ctx.obj['documents']]
              if keys]

    for j, (doc, keys) in enumerate(failed):
        logger.info('%s {c.Back.BLACK}{c.Fore.RED}%-80.80s{c.Style.RESET_ALL}',
                    j, papis.document.describe(doc))
        for k in keys:
            logger.info('\tmissing: %s', k)


@cli.command('filter-cited')
@click.help_option('-h', '--help')
@click.option('-f', '--file', '_files',
              help="Text file to check for references",
              multiple=True, required=True, type=str)
@click.pass_context
def _filter_cited(ctx: click.Context, _files: List[str]) -> None:
    """
    Filter cited documents from the read bib file
    e.g.
        papis bibtex read main.bib filter-cited -f main.tex save cited.bib
    """
    found = []

    for f in _files:
        with open(f) as fd:
            text = fd.read()
            for doc in ctx.obj['documents']:
                if re.search(doc["ref"], text):
                    found.append(doc)

    logger.info('%s documents cited', len(found))
    ctx.obj["documents"] = found


@cli.command('iscited')
@click.help_option('-h', '--help')
@click.option('-f', '--file', '_files',
              help="Text file to check for references",
              multiple=True, required=True, type=str)
@click.pass_context
def _iscited(ctx: click.Context, _files: List[str]) -> None:
    """
    Check which documents are not cited
    e.g. papis bibtex iscited -f main.tex -f chapter-2.tex
    """
    unfound = []

    for f in _files:
        with open(f) as fd:
            text = fd.read()
            for doc in ctx.obj['documents']:
                if not re.search(doc["ref"], text):
                    unfound.append(doc)

    logger.info('%s documents not cited', len(unfound))

    for j, doc in enumerate(unfound):
        logger.info('%s {c.Back.BLACK}{c.Fore.RED}%-80.80s{c.Style.RESET_ALL}',
                    j, papis.document.describe(doc))


@cli.command('import')
@click.help_option('-h', '--help')
@click.option('-o', '--out', help="Out folder to export", default=None)
@papis.cli.all_option()
@click.pass_context
def _import(ctx: click.Context, out: Optional[str], _all: bool) -> None:

    """
    Import documents to papis
        e.g. papis bibtex read mybib.bib import
    """
    docs = ctx.obj['documents']

    if not _all:
        docs = papis.api.pick_doc(docs)

    if out is not None:
        logging.info("Setting lib name to %s", out)
        if not os.path.exists(out):
            os.makedirs(out)
        config.set_lib_from_name(out)

    for j, doc in enumerate(docs):
        fileValue = None
        filepaths = []
        for k in ["file", "FILE"]:
            logger.info(
                    '%s {c.Back.BLACK}{c.Fore.YELLOW}%-80.80s'
                    '{c.Style.RESET_ALL}',
                    j, papis.document.describe(doc))
            if doc.has(k):
                fileValue = doc[k]
                logger.info("\tKey '%s' exists", k)
                break

        if not fileValue:
            logger.info("\t"
                        "{c.Back.YELLOW}{c.Fore.BLACK}"
                        "No pdf files will be imported"
                        "{c.Style.RESET_ALL}")
        else:
            filepaths = [f for f in fileValue.split(":") if os.path.exists(f)]

        if not filepaths and fileValue is not None:
            logger.info("\t"
                        "{c.Back.BLACK}{c.Fore.RED}"
                        "No valid file in \n%s{c.Style.RESET_ALL}",
                        fileValue)
        else:
            logger.info("\tfound %s file(s)", len(filepaths))

        papis.commands.add.run(filepaths, data=doc)
