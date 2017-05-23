import os
import glob
import logging
import papis.utils
import papis.config
import argparse

COMMANDS = [
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
default_parser = None
subparsers = None


def get_default_parser():
    global default_parser
    if default_parser is None:
        default_parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description="Simple documents administration program"
        )
    return default_parser


def get_subparsers():
    global subparsers
    if subparsers is None:
        SUBPARSER_HELP = "For further information for every "\
                         "command, type in 'papis <command> -h'"
        subparsers = get_default_parser().add_subparsers(
            help=SUBPARSER_HELP,
            metavar="command",
            dest="command"
        )
    return subparsers


def init_internal_commands():
    global COMMANDS
    global logger
    commands = dict()
    cmd = None
    logger.debug("Initializing commands")
    for command in COMMANDS:
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
    commands = dict()
    commands.update(init_internal_commands())
    commands.update(init_external_commands())
    return commands


class Command(object):

    args = None
    subparsers = None

    def __init__(self):
        self.default_parser = get_default_parser()
        self.parser = None
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
