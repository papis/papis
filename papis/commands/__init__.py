import logging
import papis.utils

COMMANDS = [
    "add",
    "check",
    "config",
    "edit",
    "export",
    "list",
    "rm",
    "open",
    "browse",
    "test",
    "update",
    "run",
    "sync"
]

logger = logging.getLogger("commands")


def init(parser):
    """TODO: Docstring for init.

    :parser: TODO
    :returns: TODO

    """
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


class Command(object):

    args = None
    subparser = None

    def __init__(self, parser=None):
        self.parser = parser
        self.logger = logging.getLogger(self.__class__.__name__)

    def init(self):
        pass

    def setParser(self, parser):
        """TODO: Docstring for setParser.

        :parser: TODO
        :returns: TODO

        """
        self.parser = parser

    def getParser(self):
        """TODO: Docstring for getParser.
        :returns: TODO

        """
        return self.parser

    def pick(self, folders, config, strip=""):
        """TODO: Docstring for pick.

        :folders: TODO
        :config: TODO
        :strip: TODO
        :returns: TODO

        """
        return strip+papis.utils.pick(
            [f.replace(strip, "") for f in folders],
            config
        )

    def main(self, config=None, args=None):
        if not args:
            self.args = args
