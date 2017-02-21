import logging

COMMANDS = [
"add",
"check",
"config",
"edit",
"export",
"list",
"open",
"test",
"update"
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
    logger.debug("Initializing commands")
    for command in COMMANDS:
        logger.debug(command)
        exec("from .%s import %s"%(command, command.capitalize()))
        commands[command] = eval(command.capitalize())(parser)
    return commands

class Command(object):

    def __init__(self, parser):
        self.parser = parser
        self.args = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.init(self.parser)

    def init(self):
        pass

    def main(self, config=None, args=None):
        if not args:
            self.args = args
