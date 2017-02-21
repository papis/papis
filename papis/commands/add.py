from ..document import Paper
import papis
import sys
import os
import papis.utils
from . import Command

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
        self.logger.debug("Using directory %s"%papersDir)
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
        self.logger.debug("Folder    = % s" % folderName)
        self.logger.debug("File      = % s" % paperPath)
        self.logger.debug("EndFile   = % s" % endPaperPath)
        self.logger.debug("Data      = % s" % data)
        self.logger.debug("Ext.      = % s" % extension)
        fullDirPath = os.path.join(papersDir, folderName)
        if not os.path.isdir(fullDirPath):
            self.logger.debug("Creating directory '%s'"%fullDirPath)
            os.mkdir(fullDirPath)
        shutil.copy(paperPath, endPaperPath)
        paper = Paper(fullDirPath)
        paper.update(data, force = True)
        paper.save()
