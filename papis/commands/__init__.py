import logging

logger = logging.getLogger("commands")
logger.debug("importing")

import os
import papis.utils
import papis.config
COMMAND_NAMES = [
    "default",
    "add",
    "check",
    "config",
    "edit",
    "export",
    "explore",
    "list",
    "rm",
    "mv",
    "rename",
    "open",
    "browse",
    "update",
    "run",
    "git",
    "gui",
    "sync"
]

DEFAULT_PARSER = None
SUBPARSERS = None
COMMANDS = None
ARGS = None


def set_args(args):
    """
    Set general command line arguments, this can be used also for testing.

    :param args: Arguments
    :type  args: Argument object
    """
    global ARGS
    global logger
    logger.debug("Setting args")
    ARGS = args


def set_commands(commands):
    """
    Set general initialized commands.

    :param commands: List of initialized command objects
    :type  commands: List
    """
    global COMMANDS
    logger.debug("Setting commands")
    COMMANDS = commands


def get_commands(command=None):
    """
    Get general initialized commands.

    :param command: Command that should be returned.
    :type  command: str
    >>> get_commands() is not None
    True
    >>> type(get_commands()) is dict
    True
    >>> 'add' in get_commands().keys()
    True
    """
    global COMMANDS
    if COMMANDS is None:
        init_commands()
    if command is None:
        return COMMANDS
    else:
        return COMMANDS[command]


def list_commands():
    """List all available commands
    :returns: List containing the names of the commands
    :rtype:  list

    >>> len(list_commands()) > 0
    True
    >>> type(list_commands()) is list
    True
    >>> 'add' in list_commands() and 'open' in list_commands()
    True
    >>> 'default' in list_commands()
    False
    >>> 'external' in list_commands()
    False
    """
    return [
        cmd for cmd in get_commands().keys()
        if cmd not in ['default', 'external']
    ]


def get_args():
    """
    Get general command line arguments.
    """
    global ARGS
    return ARGS


def get_default_parser():
    import argparse
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


def get_command_class_by_name(name):
    """This returns returns a command class ready to be initialised

    :param name: Name of the command, e.g., add
    :type  name: str
    :returns: A command not initialized
    :rtype: papis.commands.Command
    """
    exec("import papis.commands.%s" % (name))
    return eval("papis.commands.%s.Command" % name)


def init_internal_commands():
    global COMMAND_NAMES
    global logger
    commands = dict()
    cmd = None
    logger.debug("Initializing internal commands")
    for command in COMMAND_NAMES:
        logger.debug(command)
        cmd = get_command_class_by_name(command)()
        cmd.init()
        commands[command] = cmd
    return commands


def init_external_commands():
    import glob
    from papis.commands.external import Command as External
    logger.debug("Initializing external commands")
    commands = dict()
    paths = []
    paths.append(papis.config.get_scripts_folder())
    paths += os.environ["PATH"].split(":")
    for path in paths:
        scripts = glob.glob(os.path.join(path, "papis-*"))
        if len(scripts):
            for script in scripts:
                cmd = External()
                logger.debug(script)
                cmd.init(script)
                commands[cmd.get_command_name()] = cmd
    logger.debug("Initializing external commands done")
    return commands


def init_commands():
    """Initialize all the commands
    """
    commands = dict()
    commands.update(init_internal_commands())
    commands.update(init_external_commands())
    set_commands(commands)


def init():
    import argcomplete
    if get_commands() is not None:
        raise RuntimeError("Commands are already initialised")
    init_commands()
    # autocompletion
    argcomplete.autocomplete(get_default_parser())
    return get_commands()


def main(input_args=[]):
    commands = get_commands()
    # Parse arguments
    args = get_default_parser().parse_args(input_args or None)
    set_args(args)
    logger.debug("running main")
    commands["default"].main()


def init_and_return_parser():
    """This function is here for the automatic documentation of the
    subcommands.
    :returns: General command line parser
    """
    try:
        init()
    except Exception:
        pass
    finally:
        return get_default_parser()


class Command(object):

    parser = None
    args = None

    def __init__(self):
        self.default_parser = get_default_parser()
        self.subparsers = get_subparsers()
        self.logger = logging.getLogger(self.__class__.__name__)

    def init(self):
        pass

    def main(self):
        pass

    def add_search_argument(self):
        self.parser.add_argument(
            "search",
            help="Search query string",
            nargs="?",
            default=".",
            action="store"
        )

    def add_git_argument(
            self,
            flags=['--git'],
            help="Run command involving git",
            action=None
            ):
        action = action or ('store_false' if papis.config.get('use-git')
                                else 'store_true')
        self.parser.add_argument(
            *flags,
            help=help,
            action=action
        )

    def set_args(self, args):
        self.args = args

    def set_parser(self, parser):
        self.parser = parser

    def set_subparsers(self, subparsers):
        self.subparsers = subparsers

    def get_config(self):
        """Get configuration for the whole papis. It just simply retrieves the
        general configuration using the main ``papis.config`` API.

        :returns: General configuration
        :rtype: dict
        """
        return papis.config.get_configuration()

    def get_parser(self):
        return self.parser

    def get_args(self):
        return self.args

    def get_subparsers(self):
        return self.subparsers

    def pick(self, options, pick_config={}):
        import papis.api
        self.logger.debug("Picking")
        if len(options) == 0:
            return None
        if not pick_config:
            header_format = papis.config.get("header-format")
            match_format = papis.config.get("match-format")
            pick_config = dict(
                header_filter=lambda x: papis.utils.format_doc(header_format, x),
                match_filter=lambda x: papis.utils.format_doc(match_format, x)
            )
        return papis.api.pick(
            options,
            pick_config
        )
