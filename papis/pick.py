import logging
import os
import sys
import papis.config
from papis.tui.app import Picker
from stevedore import extension
import papis.plugin

logger = logging.getLogger("pick")


def available_pickers():
    return pickers_mgr.entry_points_names()


def papis_pick(
        options, default_index=0,
        header_filter=lambda x: x, match_filter=lambda x: x
        ):
    if len(options) == 0:
        return ""
    if len(options) == 1:
        return options[0]

    # patch stdout to stderr if the output is not a tty (terminal)
    oldstdout = sys.stdout
    if not sys.stdout.isatty():
        sys.stdout = sys.stderr
        sys.__stdout__ = sys.stderr

    picker = Picker(
        options,
        default_index,
        header_filter,
        match_filter
    )
    picker.run()
    result = picker.options_list.get_selection()

    # restore the stdout to normality
    sys.stdout = oldstdout
    sys.__stdout__ = oldstdout

    return result


pickers_mgr = extension.ExtensionManager(
    namespace='papis.picker',
    invoke_on_load=False,
    verify_requirements=True,
    propagate_map_exceptions=True,
    on_load_failure_callback=papis.plugin.stevedore_error_handler
)


def pick(
        options,
        default_index=0,
        header_filter=lambda x: x,
        match_filter=lambda x: x
        ):
    """Construct and start a :class:`Picker <Picker>`.
    """
    name = papis.config.get("picktool")
    try:
        picker = pickers_mgr[name].plugin
    except KeyError:
        logger.error("Invalid picker ({0})".format(name))
        logger.error(
            "Registered pickers are: {0}".format(available_pickers()))
    else:
        return picker(
            options,
            default_index=default_index,
            header_filter=header_filter,
            match_filter=match_filter
        )


def pick_doc(documents):
    """Pick a document from documents with the correct formatting

    :documents: List of documents
    :returns: Document

    """
    header_format_path = papis.config.get('header-format-file')
    if header_format_path is not None:
        with open(os.path.expanduser(header_format_path)) as fd:
            header_format = fd.read()
    else:
        header_format = papis.config.get("header-format")
    match_format = papis.config.get("match-format")
    pick_config = dict(
        header_filter=lambda x: papis.utils.format_doc(header_format, x),
        match_filter=lambda x: papis.utils.format_doc(match_format, x)
    )
    return pick(documents, **pick_config)
