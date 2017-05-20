import os
import glob
import logging
import papis.utils
import papis.config

COMMANDS = [
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


def init_internal_commands(parser):
    global COMMANDS
    global logger
    commands = dict()
    cmd = None
    logger.debug("Initializing commands")
    for command in COMMANDS:
        logger.debug(command)
        exec("from .%s import %s" % (command, command.capitalize()))
        cmd = eval(command.capitalize())(parser)
        cmd.setParser(parser)
        cmd.init()
        commands[command] = cmd
    return commands


def init_external_commands(parser):
    from .external import External
    commands = dict()
    paths = []
    paths.append(papis.config.get_scripts_folder())
    paths += os.environ["PATH"].split(":")
    for path in paths:
        scripts = glob.glob(os.path.join(path, "papis-*"))
        if len(scripts):
            for script in scripts:
                cmd = External(parser)
                cmd.init(script)
                commands[cmd.get_command_name()] = cmd
    return commands


def init(parser):
    commands = dict()
    commands.update(init_internal_commands(parser))
    commands.update(init_external_commands(parser))
    return commands


class Command(object):

    args = None
    subparser = None

    def __init__(self, parser=None):
        self.parser = parser
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = papis.config.get_configuration()

    def init(self):
        pass

    def set_args(self, args):
        self.args = args

    def setParser(self, parser):
        self.parser = parser

    def getParser(self):
        return self.parser

    def pick(self, options, pick_config={}):
        default_header_format =\
            "{doc.title:<70.70}|{doc.author:<20.20} ({doc.year:<4})"
        default_match_format =\
            "{doc.subfolder}{doc.title}{doc.author}{doc.year}"
        if not pick_config:
            if "header_format" in self.config[self.args.lib].keys():
                header_format = self.config[self.args.lib]["header_format"]
            else:
                header_format = default_header_format
            if "match_format" in self.config[self.args.lib].keys():
                match_format = self.config[self.args.lib]["match_format"]
            else:
                match_format = default_match_format
            pick_config = dict(
                header_filter=lambda x: header_format.format(doc=x),
                match_filter=lambda x: match_format.format(doc=x)
            )
        return papis.utils.pick(
            options,
            self.config,
            pick_config
        )

    def main(self, args=None):
        if not args:
            self.args = args
