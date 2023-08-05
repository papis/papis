from typing import Optional, Any, Callable, List

import click

import papis.config
import papis.pick
import papis.document
import papis.database


DecoratorCallable = Callable[..., Any]


def query_argument(**attrs: Any) -> DecoratorCallable:
    """Adds a ``query`` argument as a :mod:`click` decorator."""
    return click.argument(
        "query",
        default=lambda: papis.config.getstring("default-query-string"),
        type=str,
        **attrs)


def query_option(**attrs: Any) -> DecoratorCallable:
    """Adds a ``-q``, ``--query`` option as a :mod:`click` decorator."""

    return click.option(
        "-q", "--query",
        default=lambda: papis.config.getstring("default-query-string"),
        type=str,
        help="Query for a document in the database",
        **attrs)


def sort_option(**attrs: Any) -> DecoratorCallable:
    """Adds a ``--sort`` and a ``--reverse`` option as a :mod:`click` decorator."""
    def decorator(f: DecoratorCallable) -> Any:
        sort = click.option(
            "--sort", "sort_field",
            default=lambda: papis.config.get("sort-field"),
            help="Sort documents with respect to the FIELD",
            metavar="FIELD",
            **attrs)
        reverse = click.option(
            "--reverse", "sort_reverse",
            help="Reverse sort order",
            default=lambda: papis.config.getboolean("sort-reverse"),
            is_flag=True)

        return sort(reverse(f))

    return decorator


def doc_folder_option(**attrs: Any) -> DecoratorCallable:
    """Adds a ``--doc-folder`` argument as a :mod:`click` decorator."""
    return click.option(
        "--doc-folder",
        default=None,
        type=click.Path(exists=True),
        help="Document folder on which to apply action",
        **attrs)


def all_option(**attrs: Any) -> DecoratorCallable:
    """Adds a ``--all`` option as a :mod:`click` decorator."""
    return click.option(
        "-a", "--all", "_all",
        default=False,
        is_flag=True,
        help="Apply action to all matching documents",
        **attrs)


def git_option(**attrs: Any) -> DecoratorCallable:
    """Adds a ``--git`` option as a :mod:`click` decorator."""
    help = attrs.pop("help", "Commit changes to git")
    return click.option(
        "--git/--no-git",
        default=lambda: bool(papis.config.get("use-git")),
        help=help,
        **attrs)


def handle_doc_folder_or_query(
        query: str,
        doc_folder: Optional[str]) -> List[papis.document.Document]:
    """Query database for documents.

    This handles the :func:`query_option` and :func:`doc_folder_option`
    command-line arguments. If a *doc_folder* is given, then the document at
    that location is loaded, otherwise the database is queried using *query*.

    :param query: a database query string.
    :param doc_folder: existing document folder (see
        :func:`papis.document.from_folder`).
    """
    if doc_folder:
        return [papis.document.from_folder(doc_folder)]
    return papis.database.get().query(query)


def handle_doc_folder_query_sort(
        query: str,
        doc_folder: Optional[str],
        sort_field: Optional[str],
        sort_reverse: bool) -> List[papis.document.Document]:
    """Query database for documents.

    Similar to :func:`handle_doc_folder_or_query`, but also handles the
    :func:`sort_option` arguments. It sorts the resulting documents according
    to *sort_field* and *reverse_field*.

    :param sort_field: field by which to sort the resulting documents
        (see :func:`papis.document.sort`).
    :param sort_reverse: if *True*, the fields are sorted in reverse order.
    """
    documents = handle_doc_folder_or_query(query, doc_folder)

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    return documents


def handle_doc_folder_query_all_sort(
        query: str,
        doc_folder: str,
        sort_field: Optional[str],
        sort_reverse: bool,
        _all: bool) -> List[papis.document.Document]:
    """Query database for documents.

    Similar to :func:`handle_doc_folder_query_sort`, but also handles the
    :func:`all_option` argument.

    :param _all: if *False*, the user is prompted to pick a subset of documents
        (see :func:`papis.api.pick_doc`).
    """
    documents = handle_doc_folder_query_sort(query,
                                             doc_folder,
                                             sort_field,
                                             sort_reverse)

    if not _all:
        documents = [doc for doc in papis.pick.pick_doc(documents) if doc]

    return documents


def bypass(
        group: click.Group,
        command: click.Command,
        command_name: str) -> Callable[..., Any]:
    """Overwrite existing ``papis`` commands.

    This function is specially important for developing scripts in ``papis``.

    For example, consider augmenting the ``add`` command, as seen
    when using ``papis add``. In this case, we may want to add some additional
    options or behaviour before calling ``papis.commands.add``, but would like
    to avoid writing it from scratch. This function can then be used as follows
    to allow this

    .. code:: python

        import click
        import papis.cli
        import papis.commands.add

        @click.group()
        def main():
            \"\"\"Your main app\"\"\"
            pass

        @papis.cli.bypass(main, papis.commands.add.cli, "add")
        def add(**kwargs):
            # do some logic here...
            # and call the original add command line function by
            papis.commands.add.cli.bypassed(**kwargs)
    """
    group.add_command(command, command_name)

    def _decorator(new_callback: Callable[..., Any]) -> None:
        command.bypassed = command.callback     # type: ignore[attr-defined]
        command.callback = new_callback
    return _decorator
