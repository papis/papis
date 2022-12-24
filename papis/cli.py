from typing import Optional, Any, Callable, List

import click
import click.core
import click.types
import click.decorators

import papis.config
import papis.pick
import papis.document
import papis.database


DecoratorCallable = Callable[..., Any]
DecoratorArgs = Any


def query_option(**attrs: DecoratorArgs) -> DecoratorCallable:
    """Adds a ``query`` argument as a decorator"""
    def decorator(f: DecoratorCallable) -> Any:
        attrs.setdefault(
            "default",
            lambda: papis.config.get("default-query-string"))
        return click.decorators.argument("query", **attrs)(f)
    return decorator


def sort_option(**attrs: DecoratorArgs) -> DecoratorCallable:
    """Adds a ``sort`` argument as a decorator"""
    def decorator(f: DecoratorCallable) -> Any:
        attrs.setdefault("default", lambda: papis.config.get("sort-field"))
        attrs.setdefault("help", "Sort documents with respect to FIELD")
        attrs.setdefault("metavar", "FIELD")
        sort_f = click.decorators.option("--sort", "sort_field", **attrs)
        reverse_f = click.decorators.option(
            "--reverse", "sort_reverse",
            help="Reverse sort order", is_flag=True)
        return sort_f(reverse_f(f))
    return decorator


def doc_folder_option(**attrs: DecoratorArgs) -> DecoratorCallable:
    """Adds a ``document folder`` argument as a decorator"""
    def decorator(f: DecoratorCallable) -> Any:
        attrs.setdefault("default", None)
        attrs.setdefault("type", click.types.Path(exists=True))
        attrs.setdefault("help", "Apply action to a document path")
        return click.decorators.option("--doc-folder", **attrs)(f)
    return decorator


def handle_doc_folder_or_query(
        query: str,
        doc_folder: str) -> List[papis.document.Document]:
    """
    If doc_folder is given then give a list with this document.
    Else just query the database for a list of documents.
    """
    if doc_folder:
        return [papis.document.from_folder(doc_folder)]
    return papis.database.get().query(query)


def handle_doc_folder_query_sort(
        query: str,
        doc_folder: str,
        sort_field: Optional[str],
        sort_reverse: bool) -> List[papis.document.Document]:
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
    documents = handle_doc_folder_query_sort(query,
                                             doc_folder,
                                             sort_field,
                                             sort_reverse)

    if not _all:
        documents = [doc for doc in papis.pick.pick_doc(documents) if doc]

    return documents


def all_option(**attrs: DecoratorArgs) -> DecoratorCallable:
    """Adds a ``query`` argument as a decorator"""
    def decorator(f: DecoratorCallable) -> Any:
        attrs.setdefault("default", False)
        attrs.setdefault("is_flag", True)
        attrs.setdefault("help", "Apply action to all matching documents")
        return click.decorators.option("-a", "--all", "_all", **attrs)(f)
    return decorator


def git_option(
        help: str = "Add git interoperability",
        **attrs: DecoratorArgs) -> DecoratorCallable:
    """Adds a ``git`` option as a decorator"""
    def decorator(f: DecoratorCallable) -> Any:
        attrs.setdefault(
            "default",
            lambda: True if papis.config.get("use-git") else False)
        attrs.setdefault("help", help)
        return click.decorators.option("--git/--no-git", **attrs)(f)
    return decorator


def bypass(
        group: click.core.Group,
        command: click.core.Command,
        command_name: str) -> Callable[..., Any]:
    """
    This function is specially important for people developing scripts in
    papis.

    Suppose you're writing a plugin that uses the ``add`` command as seen
    in the command line in papis. However you don't want exactly the ``add``
    command and you want to add some behavior before calling it, and you
    don't want to write your own ``add`` function from scratch.

    You can then use the following snippet

    .. code::python

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
