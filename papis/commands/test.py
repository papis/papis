from ..document import Paper


def init(subparsers):
    """TODO: Docstring for init.

    :subparser: TODO
    :returns: TODO

    """
    # test parser
    test_parser = subparsers.add_parser("test",
            help="For testing (ignore)")

def main(config, args):
    """
    Main action if the command is triggered

    :config: User configuration
    :args: CLI user arguments
    :returns: TODO

    """
    papersDir = os.path.expanduser(config[args.lib]["dir"])
    printv("Using directory %s"%papersDir)
    pickFile(["1","3"], config)
