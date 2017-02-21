from ..document import Paper
from .commands import Command

class Add(Command):
    def init(self, parser):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        # add parser
        add_parser = parser.add_parser("add",
                help="Add a paper into a given library")
        add_parser.add_argument("paper",
                help="Paper file name",
                default="",
                nargs="?",
                action="store")
        add_parser.add_argument("--name",
            help    = "Name for the main folder of the paper",
            default = "",
            action  = "store"
        )
        add_parser.add_argument("--from-bibtex",
            help    = "Parse information from a bibtex file",
            default = "",
            action  = "store"
        )
        add_parser.add_argument("--from-url",
            help    = "Get paper and information from a given url, a parser must be implemented",
            default = "",
            action  = "store"
        )

    def main(self, config, args):
        """
        Main action if the command is triggered

        :config: User configuration
        :args: CLI user arguments
        :returns: TODO

        """
        papersDir = os.path.expanduser(config[args.lib]["dir"])
        printv("Using directory %s"%papersDir)
        if args.from_url:
            url = args.from_url
            service = getUrlService(url)
            try:
                serviceParser = eval("add_from_%s"%service)
            except:
                print("No add_from_%s function has been implemented, sorry"%service)
                sys.exit(1)
            paperPath, data = serviceParser(url)
        else:
            paperPath = args.paper
            data  = bibTexToDict(args.from_bibtex) \
                    if args.from_bibtex else dict()
        m = re.match(r"^(.*)\.([a-zA-Z]*)$", os.path.basename(paperPath))
        extension    = m.group(2) if m else ""
        folderName   = m.group(1) if m else os.path.basename(paperPath)
        folderName   = folderName if not args.name else args.name
        paperName    = "paper."+extension
        endPaperPath = os.path.join(papersDir, folderName, paperName )
        ######
        data["file"] = paperName
        printv("Folder    = % s" % folderName)
        printv("File      = % s" % paperPath)
        printv("EndFile   = % s" % endPaperPath)
        printv("Data      = % s" % data)
        printv("Ext.      = % s" % extension)
        fullDirPath = os.path.join(papersDir, folderName)
        if not os.path.isdir(fullDirPath):
            printv("Creating directory '%s'"%fullDirPath)
            os.mkdir(fullDirPath)
        shutil.copy(paperPath, endPaperPath)
        paper = Paper(fullDirPath)
        paper.update(data, force = True)
        paper.save()
