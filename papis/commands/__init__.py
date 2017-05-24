import os
import glob
import logging
import papis.utils
import papis.config
import argparse
import argcomplete

COMMAND_NAMES = [
    "default",
    "add",
    "check",
    "config",
    "edit",
    "export",
    "list",
    "rm",
    "mv",
    "open",
    "browse",
    "update",
    "run",
    "sync"
]

logger = logging.getLogger("commands")
DEFAULT_PARSER = None
SUBPARSERS = None
COMMANDS = None
ARGS = None


def set_args(args):
    global ARGS
    global logger
    logger.debug("Setting args")
    if ARGS is None:
        ARGS = args


def set_commands(commands):
    global COMMANDS
    logger.debug("Setting commands")
    COMMANDS = commands


def get_commands():
    global COMMANDS
    return COMMANDS


def get_args():
    global ARGS
    global logger
    return ARGS


def get_default_parser():
    global DEFAULT_PARSER
    global logger
    if DEFAULT_PARSER is None:
        DEFAULT_PARSER = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description="Simple documents administration program"
        )
    return DEFAULT_PARSER


def get_subparsers():
    global SUBPARSERS
    global logger
    if SUBPARSERS is None:
        SUBPARSER_HELP = "For further information for every "\
                         "command, type in 'papis <command> -h'"
        SUBPARSERS = get_default_parser().add_subparsers(
            help=SUBPARSER_HELP,
            metavar="command",
            dest="command"
        )
    return SUBPARSERS


def init_internal_commands():
    global COMMAND_NAMES
    global logger
    commands = dict()
    cmd = None
    logger.debug("Initializing commands")
    for command in COMMAND_NAMES:
        logger.debug(command)
        exec("from .%s import %s" % (command, command.capitalize()))
        cmd = eval(command.capitalize())()
        cmd.init()
        commands[command] = cmd
    return commands


def init_external_commands():
    from .external import External
    commands = dict()
    paths = []
    paths.append(papis.config.get_scripts_folder())
    paths += os.environ["PATH"].split(":")
    for path in paths:
        scripts = glob.glob(os.path.join(path, "papis-*"))
        if len(scripts):
            for script in scripts:
                cmd = External()
                cmd.init(script)
                commands[cmd.get_command_name()] = cmd
    return commands


def init():
    if get_commands() is not None:
       raise RuntimeError("Commands are already initialised")
    commands = dict()
    commands.update(init_internal_commands())
    commands.update(init_external_commands())
    set_commands(commands)
    return commands


def main():
    commands = get_commands()
    # autocompletion
    argcomplete.autocomplete(get_default_parser())
    # Parse arguments
    args = get_default_parser().parse_args()
    set_args(args)
    commands["default"].main()


class Command(object):

    def __init__(self):
        self.default_parser = get_default_parser()
        self.parser = None
        self.args = None
        self.subparsers = get_subparsers()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = papis.config.get_configuration()

    def init(self):
        pass

    def main(self):
        pass

    def set_args(self, args):
        self.args = args

    def set_parser(self, parser):
        self.parser = parser

    def set_subparsers(self, subparsers):
        self.subparsers = subparsers

    def get_parser(self):
        return self.parser

    def get_subparsers(self):
        return self.subparsers

    def pick(self, options, pick_config={}):
        self.logger.debug("Picking")
        if not pick_config:
            header_format = papis.config.get_header_format()
            match_format = papis.config.get_match_format()
            pick_config = dict(
                header_filter=lambda x: header_format.format(doc=x),
                match_filter=lambda x: match_format.format(doc=x)
            )
        return papis.utils.pick(
            options,
            self.config,
            pick_config
        )
