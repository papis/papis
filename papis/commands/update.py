import papis
import os
import shutil
import papis.utils
import papis.bibtex
import papis.downloaders.utils


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
            "-d",
            "--document",
            help="Overwrite an existing document",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--from-url",
            help="Get document or information from url",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "document",
            help="Document search",
            nargs="?",
            default=".",
            action="store"
        )

    def main(self):
        documents = papis.utils.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().document
        )
        document = self.pick(documents)
        data = papis.bibtex.bibtex_to_dict(self.args.from_bibtex) \
            if self.args.from_bibtex else dict()
        if self.args.from_url:
            url_data = papis.downloaders.utils.get(self.args.from_url)
            data.update(url_data["data"])
            document_paths = url_data["documents_paths"]
            if not len(document_paths) == 0:
                document_path = document_paths[0]
                old_doc = self.pick(document["files"])
                if not input("Really replace document %s? (Y/n): " % old_doc) in ["N", "n"]:
                    new_path = os.path.join(
                        document.get_main_folder(), old_doc
                    )
                    self.logger.debug(
                        "Moving %s to %s" %(document_path, new_path)
                    )
                    shutil.move(document_path, new_path)
        document.update(data, self.args.force, self.args.interactive)
        document.save()
