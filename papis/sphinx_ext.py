"""A collection of Papis-specific Sphinx extensions.

This can be included directly into the ``conf.py`` file as a normal extension, i.e.

.. code:: python

    extensions = [
        ...,
        "papis.sphinx_ext",
    ]

It will include a custom :class:`~papis.sphinx_ext.CustomClickDirective` for
documenting ``papis`` commands and a :class:`~papis.sphinx_ext.PapisConfig` directive
for documenting Papis configuration values.

These are included by default when adding it to the ``extensions`` list in your
Sphinx configuration.
"""

import os
import sys
import docutils
from typing import Any, Callable, ClassVar, Dict, List, Optional

from sphinx import application
from sphinx_click.ext import ClickDirective
from docutils.parsers.rst import Directive


class CustomClickDirective(ClickDirective):     # type: ignore[misc]
    """A custom
    `sphinx_click.ClickDirective <https://sphinx-click.readthedocs.io/en/latest/>`__
    that removes the automatic title from the generated documentation. Otherwise it
    can be used in the exact same way, e.g.::

        .. click:: papis.commands.add:cli
            :prog: papis add
    """

    def run(self) -> Any:
        sections = super().run()

        # NOTE: just remove the title section so we can add our own
        return sections[0].children[1:]


class PapisConfig(Directive):
    """A directive for describing Papis configuration values.

    The directive is given as::

        .. papis-config:: config-value-name

    and has the following optional arguments.

    * ``:section:``: The section in which the configuration value is given. The
      section defaults to :func:`~papis.config.get_general_settings_name`.
    * ``:type:``: The type of the configuration value, e.g. a string or an integer.
      If not provided, the type of the default value is used.
    * ``:default:``: The default value for the configuration value. If not
      provided, this is taken from the default Papis settings.

    It can be used as:

    .. code-block:: rst

        .. papis-config:: info-file
            :default: info.yml
            :type: str
            :section: settings

            This is the file name for where the document metadata should be
            stored. It is a relative path in the document's main folder.

    In text, these configuration values can be referenced using standard role
    references, e.g.

    .. code-block:: rst

        The document metadata is found in its :confval:`info-file`.
    """

    #: The directive can have a longer description.
    has_content: ClassVar[bool] = True
    #: Number of optional arguments to the directive.
    optional_arguments: ClassVar[int] = 3
    #: Number of required arguments to the directive.
    required_arguments: ClassVar[int] = 1
    #: A description of the arguments, mapping names to validator functions.
    option_spec: ClassVar[Dict[str, Callable[[str], Any]]] = {
        "default": str, "section": str, "type": str
        }
    add_index: int = True

    def run(self) -> Any:
        # NOTE: these are imported to register additional config settings
        import papis.commands.bibtex    # noqa: F401

        from papis.config import get_general_settings_name, get_default_settings

        default_settings = get_default_settings()
        key = self.arguments[0]

        section = self.options.get("section", get_general_settings_name())
        default = self.options.get(
            "default",
            default_settings.get(section, {}).get(key, "<missing>"))

        # NOTE: try to get some type information for display purposes
        if "type" in self.options:
            default_type = self.options["type"].strip()
            if not default_type.startswith(":"):
                default_type = f":class:`~{default_type}`"
        elif default is not None:
            tp = type(default)
            if isinstance(default, list) and len(default) > 0:
                item_type = type(default[0]).__name__
                default_type = f":class:`~typing.List` [:class:`{item_type}`]"
            else:
                if tp.__module__ == "builtins":
                    default_type = f":class:`{tp.__name__}`"
                else:
                    default_type = f":class:`~{tp.__module__}.{tp.__name__}`"
        else:
            default_type = None

        lines = [
            f".. confval:: {key}",
            "",
            f"    :type: {default_type}"
            if default_type is not None else "",
            f"    :section: ``{section}``"
            if section != get_general_settings_name() else "",
            f"    :default: ``{default!r}``",
            "",
        ] + [f"    {line}" for line in self.content]
        self.content = docutils.statemachine.StringList(lines)

        node = docutils.nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(self.content, self.content_offset, node)

        return node.children


def make_link_resolve(
        github_project_url: str,
        revision: str) -> Callable[[str, Dict[str, Any]], Optional[str]]:
    """Create a function that can be used with ``sphinx.ext.linkcode``.

    This can be used in the ``conf.py`` file as

    .. code:: python

        linkcode_resolve = make_link_resolve("https://github.com/papis/papis", "main")

    :param github_project_url: the URL to a GitHub project to which to link.
    :param revision: the revision to which to point to, e.g. ``main``.
    """

    def linkcode_resolve(domain: str, info: Dict[str, Any]) -> Optional[str]:
        url = None
        if domain != "py" or not info["module"]:
            return url

        modname = info["module"]
        objname = info["fullname"]

        mod = sys.modules.get(modname)
        if not mod:
            return url

        obj = mod
        for part in objname.split("."):
            try:
                obj = getattr(obj, part)
            except Exception:
                return url

        import inspect

        try:
            filepath = "{}.py".format(os.path.join(*obj.__module__.split(".")))
        except Exception:
            return url

        if filepath is None:
            return url

        try:
            source, lineno = inspect.getsourcelines(obj)
        except Exception:
            return url
        else:
            linestart, linestop = lineno, lineno + len(source) - 1

        return (
            f"{github_project_url}/blob/{revision}/{filepath}#L{linestart}-L{linestop}"
        )

    return linkcode_resolve


def remove_module_docstring(app: application.Sphinx,
                            what: str,
                            name: str,
                            obj: object,
                            options: Any,
                            lines: List[str]) -> None:
    # NOTE: this is used to remove the module documentation for commands so that
    # we can show the module members in the `Developer API Reference` section
    # without the tutorial / examples parts.
    if what == "module" and ".commands." in name and options.get("members"):
        del lines[:]


def setup(app: application.Sphinx) -> Dict[str, Any]:
    from sphinx.util.docfields import Field

    app.setup_extension("sphinx_click.ext")

    app.add_directive("click", CustomClickDirective, override=True)
    app.add_directive("papis-config", PapisConfig)

    app.add_object_type(
        "confval",
        "confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
        doc_field_types=[
            Field("type", label="Type", has_arg=False, names=("type",)),
            Field("default", label="Default", has_arg=False, names=("default",)),
            Field("section", label="Section", has_arg=False, names=("section",)),
        ])

    app.connect("autodoc-process-docstring", remove_module_docstring)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
