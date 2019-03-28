import os
import glob
from stevedore import extension
import logging
import papis.config
import re


def stevedore_error_handler(manager, entrypoint, exception):
    logger = logging.getLogger('cmds:stevedore')
    logger.error("Error while loading entrypoint [%s]" % entrypoint)
    logger.error(exception)


commands_mgr = None


def _create_commands_mgr():
    global commands_mgr

    if commands_mgr is not None:
        return

    commands_mgr = extension.ExtensionManager(
        namespace='papis.command',
        invoke_on_load=False,
        verify_requirements=True,
        propagate_map_exceptions=True,
        on_load_failure_callback=stevedore_error_handler
    )


def get_external_scripts():
    regex = re.compile('.*papis-([^ .]+)$')
    paths = []
    scripts = {}
    paths.append(papis.config.get_scripts_folder())
    paths += os.environ["PATH"].split(":")
    for path in paths:
        for script in glob.glob(os.path.join(path, "papis-*")):
            m = regex.match(script)
            if m is not None:
                name = m.group(1)
                path = script
                scripts[name] = dict(
                    command_name=name,
                    path=script,
                    plugin=None
                )
    return scripts


def get_scripts():
    global commands_mgr
    _create_commands_mgr()
    scripts_dict = dict()
    for command_name in commands_mgr.entry_points_names():
        scripts_dict[command_name] = dict(
            command_name=command_name,
            path=None,
            plugin=commands_mgr[command_name].plugin
        )
    return scripts_dict
