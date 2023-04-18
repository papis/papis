r"""
This command helps to interact with ``bib`` files in your LaTeX projects.

Examples
^^^^^^^^

I use it for opening some papers for instance

::

    papis bibtex read new_papers.bib open

or to add papers to the bib

::

    papis bibtex           \
      read new_papers.bib  \ # Read bib file
      add -q einstein      \ # Pick a doc with query 'einstein' from library
      add -q heisenberg    \ # Pick a doc with query 'heisenberg' from library
      save new_papers.bib    # Save in new_papers.bib

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

    papis bibtex add -q einstein save

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

.. code:: vim

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

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.bibtex:cli
    :prog: papis bibtex
"""

import os
import re

from typing import List, Optional, Tuple
import click
import tqdm

import papis.api
import papis.database
import papis.cli
import papis.config
import papis.utils
import papis.format
import papis.tui.utils
import papis.commands
import papis.commands.explore as explore
import papis.commands.add
import papis.commands.open
import papis.commands.edit
import papis.commands.browse
import papis.commands.export
from papis.commands.update import _update_with_database
import papis.bibtex
import papis.logging

logger = papis.logging.get_logger(__name__)


papis.config.register_default_settings({"bibtex": {
    "default-read-bibfile": "",
    "auto-read": "",
    "default-save-bibfile": ""
}})

EXPLORER_MGR = explore.get_explorer_mgr()


@click.group("bibtex", cls=papis.commands.AliasedGroup, chain=True)
@click.help_option("-h", "--help")
@click.option("--noar", "--no-auto-read", "no_auto_read",
              default=False,
              is_flag=True,
              help="Do not auto read even if the configuration file says it")
@click.pass_context
def cli(ctx: click.Context, no_auto_read: bool) -> None:
    """A papis script to interact with bibtex files"""
    global EXPLORER_MGR
    ctx.obj = {"documents": []}

    if no_auto_read:
        papis.config.set("auto-read", "False", section="bibtex")
    else:
        no_auto_read = not papis.config.getboolean("auto-read", section="bibtex")

    bibfile = papis.config.get("default-read-bibfile", section="bibtex")
    if not no_auto_read and bibfile and os.path.exists(bibfile):
        logger.info("Auto-reading '%s'.", bibfile)
        EXPLORER_MGR["bibtex"].plugin.callback(bibfile)


cli.add_command(EXPLORER_MGR["bibtex"].plugin, "read")


@cli.command("add")
@click.help_option("-h", "--help")
@papis.cli.all_option()
@papis.cli.query_option()
@click.option("-r", "--refs-file",
              help=("File with references to query in the database "
                    "and then add"),
              default=None)
@click.pass_context
def _add(ctx: click.Context,
         query: str,
         _all: bool,
         refs_file: Optional[str]) -> None:
    """Add a reference to the bibtex file"""
    docs = []
    if not refs_file:
        docs = papis.api.get_documents_in_lib(search=query)
    if refs_file:
        references = []
        found = 0
        db = papis.database.get()
        logger.info("Adding and querying from reference file: '%s'.", refs_file)
        with open(refs_file) as fd:
            references = fd.readlines()
        for ref in tqdm.tqdm(iterable=references):
            cleaned_ref = ref.strip("\n\r")
            if not cleaned_ref:
                continue
            results = db.query_dict({"ref": cleaned_ref})
            found += len(results)
            if results:
                docs.extend(results)
        logger.info("Found %d / %d documents.", found, len(references))
    # do not pick if refs_file is given
    if not _all and not refs_file:
        docs = list(papis.api.pick_doc(docs))
    ctx.obj["documents"].extend(docs)


@cli.command("update")
@click.help_option("-h", "--help")
@papis.cli.all_option()
@click.option("--from", "-f", "fromdb",
              show_default=True,
              help="Update the document from the library",
              default=False, is_flag=True)
@click.option("-t", "--to",
              help="Update the library document from retrieved document",
              show_default=True,
              default=False, is_flag=True)
@click.option("-k", "--keys",
              help="Update only given keys (can be given multiple times)",
              type=str,
              multiple=True)
@click.pass_context
def _update(ctx: click.Context, _all: bool,
            fromdb: bool, to: bool, keys: List[str]) -> None:
    """Update documents from and to the library"""
    docs = click.get_current_context().obj["documents"]
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
                "{c.Fore.YELLOW}%s:\n\t'{c.Fore.RED}%-80.80s{c.Style.RESET_ALL}'",
                e, papis.document.describe(doc))
        else:
            if fromdb:
                logger.info(
                    "Updating '{c.Fore.GREEN}%-80.80s{c.Style.RESET_ALL}'",
                    papis.document.describe(doc))
                if keys:
                    docs[j].update(
                        {k: libdoc.get(k) for k in keys if k in libdoc})
                else:
                    docs[j] = libdoc
    click.get_current_context().obj["documents"] = docs


@cli.command("open")
@click.help_option("-h", "--help")
@click.pass_context
def _open(ctx: click.Context) -> None:
    """Open a document in the documents list"""
    docs = ctx.obj["documents"]
    docs = papis.api.pick_doc(docs)
    if not docs:
        return
    doc = papis.utils.locate_document_in_lib(docs[0])
    papis.commands.open.run(doc)


@cli.command("edit")
@click.help_option("-h", "--help")
@click.option("-s", "--set", "set_tuples",
              help="Update document's information with key value. "
              "The value can be a papis format.",
              multiple=True,
              type=(str, str),)
@papis.cli.all_option()
@click.pass_context
def _edit(ctx: click.Context,
          set_tuples: List[Tuple[str, str]],
          _all: bool) -> None:
    """
    Tries to find the document in the list around
    the library and then edits it.

    Examples:

        papis bibtex read article.bib edit --set __proj focal-point --all

    """
    not_found = 0
    docs = ctx.obj["documents"]
    if not docs:
        return
    if not _all:
        docs = papis.api.pick_doc(docs)
    for doc in docs:
        try:
            located = papis.utils.locate_document_in_lib(doc)
            if set_tuples:
                for k, v in set_tuples:
                    located[k] = papis.format.format(v, located)
                _update_with_database(located)
            else:
                papis.commands.edit.run(located)
        except IndexError:
            not_found += 1
            logger.warning("Document not found in library '%s': %s.",
                           papis.config.get_lib_name(),
                           papis.document.describe(doc))

    logger.info("Found %d / %d documents.", len(docs) - not_found, len(docs))


@cli.command("browse")
@click.help_option("-h", "--help")
@click.option("-k", "--key", default=None, help="doi, url, ...")
@click.pass_context
def _browse(ctx: click.Context, key: Optional[str]) -> None:
    """browse a document in the documents list"""
    docs = papis.api.pick_doc(ctx.obj["documents"])
    if key:
        papis.config.set("browse-key", key)
    if not docs:
        return
    for d in docs:
        papis.commands.browse.run(d)


@cli.command("rm")
@click.help_option("-h", "--help")
@click.pass_context
def _rm(ctx: click.Context) -> None:
    """Remove a document from the documents list"""
    click.echo("Sorry, TODO...")


@cli.command("ref")
@click.help_option("-h", "--help")
@click.option("-o", "--out", help="Output ref to a file", default=None)
@click.pass_context
def _ref(ctx: click.Context, out: Optional[str]) -> None:
    """Print the reference for a document"""
    docs = ctx.obj["documents"]
    docs = papis.api.pick_doc(docs)
    if not docs:
        return
    ref = docs[0]["ref"]
    if out:
        with open(out, "w+") as fd:
            fd.write(ref)
    else:
        click.echo(ref)


@cli.command("save")
@click.help_option("-h", "--help")
@click.argument(
    "bibfile",
    default=lambda: papis.config.get("default-save-bibfile", section="bibtex"),
    required=True, type=click.Path())
@click.option("-f", "--force", default=False, is_flag=True)
@click.pass_context
def _save(ctx: click.Context, bibfile: str, force: bool) -> None:
    """Save the documents imported in bibtex format"""
    docs = ctx.obj["documents"]
    if not force:
        c = papis.tui.utils.confirm("Are you sure you want to save?")
        if not c:
            click.echo("Not saving..")
            return
    with open(bibfile, "w+") as fd:
        logger.info("Saving %d documents in '%s'.", len(docs), bibfile)
        fd.write(papis.commands.export.run(docs, to_format="bibtex"))


@cli.command("sort")
@click.help_option("-h", "--help")
@click.option("-k", "--key",
              help="Field to order it",
              default=None,
              type=str,
              required=True)
@click.option("-r", "--reverse",
              help="Reverse the order",
              default=False,
              is_flag=True)
@click.pass_context
def _sort(ctx: click.Context, key: Optional[str], reverse: bool) -> None:
    """Sort documents"""
    docs = ctx.obj["documents"]
    ctx.obj["documents"] = list(sorted(docs,
                                       key=lambda d: str(d[key]),
                                       reverse=reverse))


@cli.command("unique")
@click.help_option("-h", "--help")
@click.option("-k", "--key",
              help="Field to test for uniqueness, default is ref",
              default="ref",
              type=str)
@click.option("-o",
              help="Output the discarded documents to a file",
              default=None,
              type=str)
@click.pass_context
def _unique(ctx: click.Context, key: str, o: Optional[str]) -> None:
    """Remove duplicate BibTeX entries."""
    docs = ctx.obj["documents"]
    unique_docs = []
    duplicated_docs = []

    while True:
        if len(docs) == 0:
            break

        doc = docs.pop(0)
        unique_docs.append(doc)
        indices = []

        doc_value = doc.get(key)
        for i, other in enumerate(docs):
            if doc_value == other.get(key):
                indices.append(i)
                duplicated_docs.append(other)
                logger.info(
                    "Found a duplicate document for key '%s' with value '%s'.\n"
                    "\t%s\n\t%s",
                    key, doc_value,
                    papis.document.describe(doc),
                    papis.document.describe(other))
        docs = [d for (i, d) in enumerate(docs) if i not in indices]

    logger.info("Found %d unique documents.", len(unique_docs))
    logger.info("Discarded %d duplicated documents.", len(duplicated_docs))

    ctx.obj["documents"] = unique_docs
    if o:
        logger.info("Saving %d duplicate documents in '%s'.", len(duplicated_docs), o)
        with open(o, "w+") as f:
            f.write(papis.commands.export.run(duplicated_docs, to_format="bibtex"))


@cli.command("doctor")
@click.help_option("-h", "--help")
@click.option("-k", "--key",
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
    logger.info("Checking for existence of keys '%s'.", "', '".join(key))

    failed = [(d, keys) for d, keys in [(d, [k for k in key if k not in d])
                                        for d in ctx.obj["documents"]]
              if keys]

    for j, (doc, keys) in enumerate(failed):
        logger.info("%d. {c.Fore.RED}%-80.80s{c.Style.RESET_ALL}",
                    j, papis.document.describe(doc))
        for k in keys:
            logger.info("\tMissing: %s", k)


@cli.command("filter-cited")
@click.help_option("-h", "--help")
@click.option("-f", "--file", "_files",
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
            for doc in ctx.obj["documents"]:
                if re.search(doc["ref"], text):
                    found.append(doc)

    logger.info("Found %d cited documents.", len(found))
    ctx.obj["documents"] = found


@cli.command("iscited")
@click.help_option("-h", "--help")
@click.option("-f", "--file", "_files",
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
            for doc in ctx.obj["documents"]:
                if not re.search(doc["ref"], text):
                    unfound.append(doc)

    logger.info("Found %s documents with no citations.", len(unfound))

    for j, doc in enumerate(unfound):
        logger.info("%d. {c.Fore.RED}%-80.80s{c.Style.RESET_ALL}",
                    j, papis.document.describe(doc))


@cli.command("import")
@click.help_option("-h", "--help")
@click.option("-o", "--out", help="Out folder to export", default=None)
@papis.cli.all_option()
@click.pass_context
def _import(ctx: click.Context, out: Optional[str], _all: bool) -> None:
    """
    Import documents to papis
        e.g. papis bibtex read mybib.bib import
    """
    docs = ctx.obj["documents"]

    if not _all:
        docs = papis.api.pick_doc(docs)

    if out is not None:
        logger.info("Setting library to '%s'.", out)
        if not os.path.exists(out):
            os.makedirs(out)
        papis.config.set_lib_from_name(out)

    for j, doc in enumerate(docs):
        file_value = None
        filepaths = []
        for k in ("file", "FILE"):
            logger.info(
                "%d. {c.Fore.YELLOW}%-80.80s{c.Style.RESET_ALL}",
                j, papis.document.describe(doc))
            if k in doc:
                file_value = doc[k]
                logger.info("\tKey '%s' exists", k)
                break

        if not file_value:
            logger.info(
                "\t{c.Fore.YELLOW}No PDF files will be imported{c.Style.RESET_ALL}.")
        else:
            filepaths = [f for f in file_value.split(":") if os.path.exists(f)]

        if not filepaths and file_value is not None:
            logger.info(
                "\t{c.Fore.RED}No valid file in '%s'{c.Style.RESET_ALL}.",
                file_value)
        else:
            logger.info("\tFound %d file(s).", len(filepaths))

        papis.commands.add.run(filepaths, data=doc)
