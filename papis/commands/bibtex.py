# -*- coding: utf-8 -*-
import os
import papis.api
import papis.cli
import click
import papis.config as config
import papis.utils
import papis.commands.explore as explore
import papis.commands.open
import papis.commands.edit
import papis.commands.browse
import papis.commands.export
import logging
import colorama
import difflib

logger = logging.getLogger('papis:bibtex')


config.register_default_settings({'bibtex': {
    'default-read-bibfile': '',
    'auto-read': '',
    'default-save-bibfile': ''
}})

explorer_mgr = explore.get_explorer_mgr()


@click.group("bibtex", cls=papis.cli.AliasedGroup, chain=True)
@click.help_option('-h', '--help')
@click.option(
    '--noar', '--no-auto-read', 'no_auto_read',
    default=False,
    is_flag=True,
    help="Do not auto read even if the configuration file says otherwise"
)
@click.pass_context
def cli(ctx, no_auto_read):
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
@click.option(
    '-a', '--all', help='Add all searched documents', default=False,
    is_flag=True)
@click.pass_context
def _add(ctx, query, all):
    """Add a refrence to the bibtex file"""
    docs = papis.api.get_documents_in_lib(search=query)
    if not all:
        docs = [papis.api.pick_doc(docs)]
    ctx.obj['documents'].extend(docs)


@cli.command('update')
@click.help_option('-h', '--help')
@click.option(
    '-a', '--all', show_default=True, help='update all searched documents',
    default=False, is_flag=True)
@click.option(
    '--from', '-f', 'fromdb',
    show_default=True,
    help='Update the document from the library',
    default=False, is_flag=True)
@click.option(
    '-t', '--to', help='Update the library document from retrieved document',
    show_default=True,
    default=False, is_flag=True)
@click.option(
    '-k', '--keys',
    help='Update only given keys (this flag can be given multiple times)',
    type=str, multiple=True)
@click.pass_context
def _update(ctx, all, fromdb, to, keys):
    """Update documents from and to the library"""
    docs = click.get_current_context().obj['documents']
    picked_doc = None
    picked_index = -1
    if not all:
        picked_doc = papis.api.pick_doc(docs)
        if picked_doc is None:
            return
        picked_index = list(map(lambda x: id(x), docs)).index(id(picked_doc))
    for j, doc in enumerate(docs):
        if not all:
            if not j == picked_index:
                continue
        try:
            libdoc = papis.utils.locate_document_in_lib(doc)
        except IndexError as e:
            logger.info(
                '{c.Fore.YELLOW}{0}: \n\t{c.Back.RED}{doc: <80.80}{c.Style.RESET_ALL}'
                .format(e, doc=papis.document.describe(doc), c=colorama)
            )
        else:
            if fromdb:
                logger.info(
                    'Updating \n\t'
                    '{c.Fore.GREEN}{c.Back.BLACK}{doc: <80.80}{c.Style.RESET_ALL}'
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
def _open(ctx):
    """Open a document in the documents list"""
    docs = ctx.obj['documents']
    doc = papis.api.pick_doc(docs)
    if not doc:
        return
    doc = papis.utils.locate_document_in_lib(doc)
    papis.commands.open.run(doc)


@cli.command('edit')
@click.help_option('-h', '--help')
@click.option(
    '-l', '--lib',
    show_default=True,
    help='Edit document in papis library',
    default=False, is_flag=True)
@click.pass_context
def _edit(ctx, lib):
    """edit a document in the documents list"""
    docs = ctx.obj['documents']
    doc = papis.api.pick_doc(docs)
    if not doc:
        return
    doc = papis.utils.locate_document_in_lib(doc)
    papis.commands.edit.run(doc)


@cli.command('rm')
@click.help_option('-h', '--help')
@click.pass_context
def _rm(ctx):
    """Remove a document from the documents list"""
    print('Sorry, TODO...')


@cli.command('ref')
@click.help_option('-h', '--help')
@click.option('-o', '--out', help='Output ref to a file', default=None)
@click.pass_context
def _ref(ctx, out):
    """Print the reference for a document"""
    docs = ctx.obj['documents']
    doc = papis.api.pick_doc(docs)
    if not doc:
        return
    ref = doc["ref"]
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
def _save(ctx, bibfile, force):
    """Save the documents imported in bibtex format"""
    docs = ctx.obj['documents']
    if not force:
        c = papis.utils.confirm('Are you sure you want to save?')
        if not c:
            print('Not saving..')
            return
    with open(bibfile, 'w+') as fd:
        logger.info('Saving {1} documents in {0}..'.format(bibfile, len(docs)))
        fd.write(papis.commands.export.run(docs, to_format='bibtex'))


@cli.command('sort')
@click.help_option('-h', '--help')
@click.option(
    '-k', '--key',
    help="Field to order it",
    default=None,
    type=str,
    required=True)
@click.option(
    '-r', '--reverse',
    help="Reverse the order",
    default=False,
    is_flag=True)
@click.pass_context
def _sort(ctx, key, reverse):
    """Save the documents imported in bibtex format"""
    docs = ctx.obj['documents']
    ctx.obj['documents'] = list(
        sorted(docs, key=lambda d: d[key], reverse=reverse))
