from ..document import Paper

def init(parser):
    """TODO: Docstring for init.

    :parser: TODO
    :returns: TODO

    """
    description="Simple papers administration program")
    parser.add_argument("--manual",
        help    = "Spit out the manual",
        default = False,
        action  = "store_true"
    )
    parser.add_argument("-v",
        "--verbose",
        help    = "Make the output verbose",
        default = False,
        action  = "store_true"
    )
    parser.add_argument("--lib",
        help    = "Choose a papers library, default general",
        default = "general",
        action  = "store"
    )


def main(config, args):
    """
    Main action if the command is triggered

    :config: User configuration
    :args: CLI user arguments
    :returns: TODO

    """
    papersDir = os.path.expanduser(config[args.lib]["dir"])
    printv("Using directory %s"%papersDir)
    if args.manual:
        print(MANUAL)
