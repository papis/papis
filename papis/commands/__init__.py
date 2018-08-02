import logging

logger = logging.getLogger("commands")
logger.debug("importing")

import sys
import os
import papis.utils
import papis.config


def get_external_scripts():
    import glob
    paths = []
    scripts = []
    paths.append(papis.config.get_scripts_folder())
    paths += os.environ["PATH"].split(":")
    for path in paths:
        scripts += glob.glob(os.path.join(path, "papis-*"))
    return scripts


def patch_external_input_args(arguments):
    """
    We have to add as the first argument to any external script a whitespace
    or something besides a flag, since in argparse that REMAINDER needs a
    non-flag argument first to work. This is a ?BUG? of argparse
    stackoverflow.com/questions/43219022/
    using-argparse-remainder-at-beginning-of-parser-sub-parser
    """
    external_names = [
        cmd.get_command_name() for cmd in get_commands().values()
        if cmd.is_external()
    ]
    for j, arg in enumerate(arguments):
        if arg in external_names:
            logger.debug("Patching {} command for argparse".format(arg))
            arguments.insert(j+1, " ")
