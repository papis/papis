import papis
import os
import papis.utils
import papis.bibtex


class Update(papis.commands.Command):
    def init(self):

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

    def main(self):
        documentsDir = os.path.expanduser(self.config[self.args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = self.args.document
        data = papis.bibtex.bibtex_to_dict(self.args.from_bibtex) \
            if self.args.from_bibtex else dict()
        documents = papis.utils.get_documents_in_dir(
            documentsDir,
            documentSearch
        )
        document = self.pick(documents)
        document.update(data, self.args.force, self.args.interactive)
        document.save()
