r"""
This command is used for interacting with BibTeX ``bib`` files in your LaTeX projects.

It is meant to be used when the BibTeX file is a companion to your Papis library.
Then, ``papis bibtex`` can be used to add, remove, update, and generally clean
the file using information from the library.

Examples
^^^^^^^^

You can use it for opening some papers from the BibTeX file by calling

.. code:: sh

    papis bibtex read new_papers.bib open

This is done by matching the entry in the BibTeX file with a document in your
library and then opening the correspond files. If no document can be found in
the library, then the file cannot be opened, of course. To add papers to the
BibTeX file (from the current library) you can call

.. code:: sh

    papis bibtex             \
        read new_papers.bib  \ # Read bib file
        add -q einstein      \ # Pick a doc with query 'einstein' from library
        add -q heisenberg    \ # Pick a doc with query 'heisenberg' from library
        save new_papers.bib    # Save in new_papers.bib

To update some information that was modified in Papis'
:ref:`YAML files <info-file>`, you can call

.. code:: sh

    papis bibtex            \
        read new_papers.bib \ # Read bib file
        update -f           \ # Update what has been read from papis library
        save new_papers.bib   # save everything to new_papers.bib, overwriting

.. note::

    Reading, adding, and then saving documents in this fashion will re-export
    them and may change the formatting of your BibTeX file.

Local configuration file
^^^^^^^^^^^^^^^^^^^^^^^^

If you are working in a local folder where you have a ``bib`` file called
``main.bib``, you can avoid adding the repetitive ``read main.bib`` and
``save main.bib`` by using the configuration values described in the
:ref:`documentation <bibtex-command-options>`. You can create a local
configuration file ``.papis.config`` for ``papis bibtex`` to read and write
automatically. This file should contain::

    [bibtex]
    default-read-bibfile = main.bib
    default-save-bibfile = main.bib
    auto-read = True

With this setup, you can just do::

    papis bibtex add -q einstein save

Check references quality
^^^^^^^^^^^^^^^^^^^^^^^^

When you're collaborating with someone, you might come across malformed
or incomplete references. Most journals want to have all the DOIs
and URLs available. For this you can use the ``doctor`` command::

    papis bibtex read mybib.bib doctor

Usually, you likely want to only have the references that are actually cited
in the LaTeX file in your project's BibTeX file. You can check which references
are not cited in the ``.tex`` files by calling::

    papis bibtex iscited -f main.tex -f chapter-2.tex

and you can then filter them out using the ``filter-cited`` command.

To monitor the health of the project's BibTeX file, you can add a simple target
to the project's ``Makefile`` like

.. code:: make

    check-bib:
        papis bibtex iscited -f main.tex doctor
    .PHONY: check-bib

Vim integration
^^^^^^^^^^^^^^^

This command can also be easily used from Vim with these simple lines

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

import papis.database
import papis.cli
import papis.config
import papis.format
import papis.logging
import papis.strings
from papis.commands import AliasedGroup
from papis.commands.explore import get_explorer_by_name

logger = papis.logging.get_logger(__name__)


papis.config.register_default_settings({"bibtex": {
    "default-read-bibfile": "",
    "auto-read": "",
    "default-save-bibfile": ""
}})

BIBTEX_EXPLORER = get_explorer_by_name("bibtex")


@click.group("bibtex", cls=AliasedGroup, chain=True)
@click.help_option("-h", "--help")
@papis.cli.bool_flag(
    "--noar", "--no-auto-read", "no_auto_read",
    help="Do not auto read the 'default-read-file' (must call 'read' explicitly)")
@click.pass_context
def cli(ctx: click.Context, no_auto_read: bool) -> None:
    """Interact with BibTeX files"""
    ctx.obj = {"documents": []}

    if no_auto_read:
        papis.config.set("auto-read", "False", section="bibtex")
    else:
        no_auto_read = not papis.config.getboolean("auto-read", section="bibtex")

    bibfile = papis.config.get("default-read-bibfile", section="bibtex")
    if not no_auto_read and bibfile and os.path.exists(bibfile):
        logger.info("Auto-reading '%s'.", bibfile)
        if BIBTEX_EXPLORER and BIBTEX_EXPLORER.callback:
            BIBTEX_EXPLORER.callback(bibfile)


if BIBTEX_EXPLORER:
    cli.add_command(BIBTEX_EXPLORER, "read")


@cli.command("add")
@click.help_option("-h", "--help")
@papis.cli.all_option()
@papis.cli.query_option()
@click.option(
    "-r", "--refs-file",
    help="File with references to query in the database and then add",
    type=click.Path(exists=True),
    default=None)
@click.pass_context
def cli_add(ctx: click.Context,
            query: str,
            _all: bool,
            refs_file: Optional[str]) -> None:
    """Add documents from the library to the BibTeX file"""
    from papis.api import get_documents_in_lib, pick_doc

    docs = []

    if refs_file:
        from papis.tui.utils import progress_bar

        db = papis.database.get()

        references = []
        found = 0
        logger.info("Adding and querying from reference file: '%s'.", refs_file)

        with open(refs_file, encoding="utf-8") as fd:
            references = fd.readlines()

        for ref in progress_bar(references):
            cleaned_ref = ref.strip("\n\r")
            if not cleaned_ref:
                continue

            results = db.query_dict({"ref": cleaned_ref})
            found += len(results)
            docs.extend(results)

        logger.info("Found %d documents for %d references.", found, len(references))
    else:
        docs = get_documents_in_lib(search=query)
        if not _all:
            docs = list(pick_doc(docs))

    ctx.obj["documents"].extend(docs)


@cli.command("update")
@click.help_option("-h", "--help")
@papis.cli.all_option()
@papis.cli.bool_flag("--from", "-f", "fromdb",
                     help="Update the document from the library")
@papis.cli.bool_flag("-t", "--to", "todb",
                     help="Update the library document from the BibTeX file")
@click.option("-k", "--keys",
              help="Update only given keys (can be given multiple times)",
              type=str,
              multiple=True)
@click.pass_context
def cli_update(ctx: click.Context, _all: bool,
               fromdb: bool, todb: bool, keys: List[str]) -> None:
    """Update documents from and to the library"""
    if fromdb and todb:
        logger.error("Cannot pass both '--from' and '--to'.")
        return

    from papis.api import pick_doc, save_doc
    from papis.utils import locate_document_in_lib

    docs = ctx.obj["documents"]

    picked_doc = None
    if not _all:
        picked_docs = pick_doc(docs)
        if not picked_docs or not picked_docs[0]:
            logger.warning(papis.strings.no_documents_retrieved_message)
            return

        picked_doc = picked_docs[0]

    libname = papis.config.get_lib_name()
    unique_document_keys = papis.config.getlist("unique-document-keys")
    logger.info("This uses the keys %s to determine a match in the library.",
                unique_document_keys)

    for j, doc in enumerate(docs):
        if picked_doc and doc["ref"] != picked_doc["ref"]:
            continue

        logger.info("Checking for BibTeX entry in the '%s' library: '%s'.",
                    libname, papis.document.describe(doc))

        try:
            libdoc = locate_document_in_lib(
                doc, libname, unique_document_keys=unique_document_keys
                )
        except IndexError:
            logger.warning(
                "No document matching the BibTeX entry found in the '%s' library.",
                libname)
            continue

        if fromdb:
            logger.info("Updating BibTeX entry from library.")
            if keys:
                docs[j].update({k: libdoc[k] for k in keys if k in libdoc})  # noqa: PLR1736
            else:
                docs[j] = libdoc.copy()

        if todb:
            logger.info("Adding BibTeX entry to library document: '%s'.",
                        papis.document.describe(libdoc))
            if keys:
                libdoc.update({k: doc[k] for k in keys if k in doc})
            else:
                libdoc.clear()
                libdoc.update(doc)
                save_doc(libdoc)

        logger.info("")

    ctx.obj["documents"] = docs


@cli.command("open")
@click.help_option("-h", "--help")
@click.pass_context
def cli_open(ctx: click.Context) -> None:
    """Open a document using the default application."""
    from papis.api import pick_doc

    docs = ctx.obj["documents"]
    docs = pick_doc(docs)

    if not docs:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    doc = docs[0]

    libname = papis.config.get_lib_name()
    unique_document_keys = papis.config.getlist("unique-document-keys")
    logger.info("Checking the '%s' library for document: '%s'",
                libname, papis.document.describe(doc))

    from papis.utils import locate_document_in_lib

    try:
        libdoc = locate_document_in_lib(
            doc, libname, unique_document_keys=unique_document_keys
        )
    except IndexError:
        logger.warning(
            "No document matching the BibTeX entry found in the '%s' library.",
            libname)
    else:
        from papis.commands.open import run

        run(libdoc)


@cli.command("edit")
@click.help_option("-h", "--help")
@click.option("-s", "--set", "set_tuples",
              help="Update a document with key value pairs",
              multiple=True,
              type=(str, papis.cli.FormattedStringParamType()),)
@papis.cli.all_option()
@click.pass_context
def cli_edit(ctx: click.Context,
             set_tuples: List[Tuple[str, str]],
             _all: bool) -> None:
    """
    Edit documents by adding keys or opening an editor.

    For example, you can run the following to add a special key ``__proj`` to
    all the documents

    .. code:: sh

        papis bibtex read article.bib edit --set __proj focal-point --all
    """
    from papis.api import pick_doc, save_doc

    docs = ctx.obj["documents"]
    if not docs:
        return

    if not _all:
        docs = pick_doc(docs)

    libname = papis.config.get_lib_name()
    unique_document_keys = papis.config.getlist("unique-document-keys")

    not_found = 0
    for doc in docs:
        try:
            located = papis.utils.locate_document_in_lib(
                doc, libname, unique_document_keys=unique_document_keys,
            )
        except IndexError:
            not_found += 1
            logger.warning("Document not found in library '%s': %s.",
                           libname,
                           papis.document.describe(doc))
            continue

        if set_tuples:
            for k, v in set_tuples:
                kp, vp = papis.strings.process_formatted_string_pair(k, v)
                try:
                    located[kp] = papis.format.format(vp, located)
                except papis.format.FormatFailedError as exc:
                    logger.error("Could not format '%s' with value '%s'.",
                                 kp, vp, exc_info=exc)

            save_doc(located)
        else:
            from papis.commands.edit import run

            run(located)

    logger.info("Found %d / %d documents.", len(docs) - not_found, len(docs))


@cli.command("browse")
@click.help_option("-h", "--help")
@click.option("-k", "--key", default=None, help="doi, url, ...")
@click.pass_context
def cli_browse(ctx: click.Context, key: Optional[str]) -> None:
    """Browse a document in the document list."""
    from papis.api import pick_doc

    docs = pick_doc(ctx.obj["documents"])
    if not docs:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if key:
        papis.config.set("browse-key", key)

    from papis.commands.browse import run

    for d in docs:
        run(d)


@cli.command("rm")
@click.help_option("-h", "--help")
@click.pass_context
def cli_rm(ctx: click.Context) -> None:
    """Remove a document from the documents list."""
    click.echo("Sorry, TODO...")


@cli.command("ref")
@click.help_option("-h", "--help")
@click.option("-o", "--out", help="Output ref to a file", default=None)
@click.pass_context
def cli_ref(ctx: click.Context, out: Optional[str]) -> None:
    """Print the reference for a document."""
    from papis.api import pick_doc

    docs = ctx.obj["documents"]
    docs = pick_doc(docs)

    if not docs:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    ref = docs[0]["ref"]
    if out:
        with open(out, "w+", encoding="utf-8") as fd:
            fd.write(ref)
    else:
        click.echo(ref)


@cli.command("save")
@click.help_option("-h", "--help")
@click.argument(
    "bibfile",
    default=lambda: papis.config.get("default-save-bibfile", section="bibtex"),
    required=True, type=click.Path())
@papis.cli.bool_flag("-f", "--force", help="Do not ask for confirmation when saving")
@click.pass_context
def cli_save(ctx: click.Context, bibfile: str, force: bool) -> None:
    """Save the documents in the BibTeX format."""
    docs = ctx.obj["documents"]

    if not force:
        from papis.tui.utils import confirm

        if not confirm("Are you sure you want to save?"):
            return

    from papis.commands.export import run

    with open(bibfile, "w+", encoding="utf-8") as fd:
        logger.info("Saving %d documents in '%s'.", len(docs), bibfile)
        fd.write(run(docs, to_format="bibtex"))


@cli.command("sort")
@click.help_option("-h", "--help")
@click.option("-k", "--key",
              help="Field to order by",
              default=None,
              type=str,
              required=True)
@papis.cli.bool_flag("-r", "--reverse", help="Reverse the sort order")
@click.pass_context
def cli_sort(ctx: click.Context, key: Optional[str], reverse: bool) -> None:
    """Sort the documents in the BibTeX file."""
    docs = ctx.obj["documents"]
    ctx.obj["documents"] = sorted(docs,
                                  key=lambda d: str(d[key]),
                                  reverse=reverse)


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
def cli_unique(ctx: click.Context, key: str, o: Optional[str]) -> None:
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

    from papis.commands.export import run

    if o:
        logger.info("Saving %d duplicate documents in '%s'.", len(duplicated_docs), o)
        with open(o, "w+", encoding="utf-8") as f:
            f.write(run(duplicated_docs, to_format="bibtex"))


@cli.command("doctor")
@click.help_option("-h", "--help")
@click.option("-k", "--key",
              help="Field to test for uniqueness, default is ref",
              multiple=True,
              default=("doi", "url", "year", "title", "author"),
              type=str)
@click.pass_context
def cli_doctor(ctx: click.Context, key: List[str]) -> None:
    """
    Check BibTeX file for correctness.

    This can check missing keys, e.g. by running

    .. code:: sh

        papis bibtex doctor -k title -k url -k doi
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
def cli_filter_cited(ctx: click.Context, _files: List[str]) -> None:
    """
    Filter cited documents from the BibTeX file.

    for example to filter cited documents in ``main.tex`` and save a unique
    list of documents in ``cited.bib``, you can run

    .. code:: sh

        papis bibtex read main.bib filter-cited -f main.tex save cited.bib
    """
    found = []

    for f in _files:
        with open(f, encoding="utf-8") as fd:
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
def cli_iscited(ctx: click.Context, _files: List[str]) -> None:
    """
    Check which documents are not cited.

    For example, to print a list of documents that have not been cited in
    both ``main.tex`` and ``chapter-2.tex``, run

    .. code:: sh

        papis bibtex iscited -f main.tex -f chapter-2.tex
    """
    unfound = []

    for f in _files:
        with open(f, encoding="utf-8") as fd:
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
def cli_import(ctx: click.Context, out: Optional[str], _all: bool) -> None:
    """
    Import documents from a BibTeX file to the current library.

    For example, you can run

    .. code:: sh

        papis bibtex read mybib.bib import
    """
    from papis.api import pick_doc

    docs = ctx.obj["documents"]

    if not _all:
        docs = pick_doc(docs)

    if out is not None:
        logger.info("Setting library to '%s'.", out)
        if not os.path.exists(out):
            os.makedirs(out)
        papis.config.set_lib_from_name(out)

    from papis.commands.add import run

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

        run(filepaths, data=doc)
