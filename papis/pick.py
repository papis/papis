import logging
import papis.config
from papis.tui.app import Picker
from stevedore import extension

logger = logging.getLogger("pick")


def stevedore_error_handler(manager, entrypoint, exception):
    logger = logging.getLogger("pick:stevedore")
    logger.error("Error while loading entrypoint [%s]" % entrypoint)
    logger.error(exception)


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

    picker = Picker(
        options,
        default_index,
        header_filter,
        match_filter
    )
    picker.run()
    return picker.options_list.get_selection()


pickers_mgr = extension.ExtensionManager(
    namespace='papis.picker',
    invoke_on_load=False,
    verify_requirements=True,
    propagate_map_exceptions=True,
    on_load_failure_callback=stevedore_error_handler
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
