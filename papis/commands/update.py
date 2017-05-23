import papis
import os
import papis.utils
import papis.bibtex


class Update(papis.commands.Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        # update parser
        self.parser = self.get_subparsers().add_parser(
            "update",
            help="Update a document from a given library"
        )
        self.parser.add_argument(
            "--from-bibtex",
            help="Update info from bibtex file",
            action="store"
        )
        self.parser.add_argument(
            "-i",
            "--interactive",
            help="Interactively update",
            default=False,
            action="store_true"
        )
        self.parser.add_argument(
            "-f",
            "--force",
            help="Force update, overwrite conflicting information",
            default=False,
            action="store_true"
        )
        self.parser.add_argument(
            "document",
            help="Document search",
            action="store"
        )

    def main(self, args):
        documentsDir = os.path.expanduser(self.config[args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        data = papis.bibtex.bibtex_to_dict(args.from_bibtex) \
            if args.from_bibtex else dict()
        documents = papis.utils.get_documents_in_dir(
            documentsDir,
            documentSearch
        )
        document = self.pick(documents)
        document.update(data, args.force, args.interactive)
        document.save()
