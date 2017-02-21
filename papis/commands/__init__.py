COMMANDS = [
"add",
"check",
"config",
"edit",
"export",
"list",
"no_command",
"open",
"test",
"update"
]

def init(parser):
    """TODO: Docstring for init.

    :parser: TODO
    :returns: TODO

    """
    global COMMANDS
    commands = dict()
    for command in COMMANDS:
        exec("from .%s import %s as cmd"%(command, command.capitalize()))
        commands[command] = cmd(parser)
    return commands

class Command(object):

    def __init__(self, parser):
        self.parser = parser
        self.args = None
        self.init(self.parser)

    def init(self):
        pass

    def main(self, args=None):
        if not args:
            self.args = args
