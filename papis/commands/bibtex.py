# -*- coding: utf-8 -*-
r"""

This command helps to interact with `bib` files in your LaTeX projects.

Examples
^^^^^^^^

::

    papis bibtex                            \
      read new_papers.bib                   \ # Read bib file
      cmd 'papis add --from-doi {doc[doi]}'   # For every entry run the command

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

Maybe this is also interesting for you guys!

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
.. click:: papis.commands.add:cli
    :prog: papis add

"""
import os
import papis.api
import papis.cli
import click
import papis.config as config
import papis.utils
import papis.tui.utils
import papis.commands.explore as explore
import papis.commands.open
import papis.commands.edit
import papis.commands.browse
import papis.commands.export
import logging
import colorama

from typing import List, Optional

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
    """A papis script to interact wit bibtex files"""
    global explorer_mgr
    ctx.obj = {'documents': []}

    if no_auto_read:
        logger.info('Setting auto-read to False')
        config.set('auto-read', 'False', section='bibtex')

    bibfile = config.get('default-read-bibfile', section='bibtex')
    if (bool(config.getboolean('auto-read', section='bibtex')) and
       bibfile and
       os.path.exists(bibfile)):
        logger.info("auto reading {0}".format(bibfile))
        explorer_mgr['bibtex'].plugin.callback(bibfile)


cli.add_command(explorer_mgr['bibtex'].plugin, 'read')


@cli.command('add')
@papis.cli.query_option()
@click.help_option('-h', '--help')
@papis.cli.all_option()
@click.pass_context
def _add(ctx: click.Context, query: str, _all: bool) -> None:
    """Add a refrence to the bibtex file"""
    docs = papis.api.get_documents_in_lib(search=query)
    if not _all:
        _docs = papis.api.pick_doc(docs)
    ctx.obj['documents'].extend(_docs)


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
        picked_doc = papis.api.pick_doc(docs)
        if picked_doc is None:
            return
    for j, doc in enumerate(docs):
        try:
            libdoc = papis.utils.locate_document_in_lib(doc)
        except IndexError as e:
            logger.info(
                '{c.Fore.YELLOW}{0}:'
                '\n\t{c.Back.RED}{doc: <80.80}{c.Style.RESET_ALL}'
                .format(e, doc=papis.document.describe(doc), c=colorama)
            )
        else:
            if fromdb:
                logger.info(
                    'Updating \n\t{c.Fore.GREEN}'
                    '{c.Back.BLACK}{doc: <80.80}{c.Style.RESET_ALL}'
                    .format(doc=papis.document.describe(doc), c=colorama)
                )
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
        papis.config.set("browse-key", key)
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
        logger.info('Saving {1} documents in {0}..'.format(bibfile, len(docs)))
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
    """Save the documents imported in bibtex format"""
    docs = ctx.obj['documents']
    ctx.obj['documents'] = list(
        sorted(docs, key=lambda d: d[key], reverse=reverse))
