"""This command edits the information of the documents.
The editor used is defined by the ``editor`` configuration setting.


"""
import papis
import os
import papis.api
import papis.utils
import papis.config
import papis.database


def run(document, editor=None, wait=True):
    if editor is not None:
        papis.config.set('editor', editor)
    database = papis.database.get()
    papis.utils.general_open(document.get_info_file(), "editor", wait=wait)
    document.load()
    database.update(document)


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "edit",
            help="Edit document information from a given library"
        )

        self.add_search_argument()

        self.parser.add_argument(
            "-n",
            "--notes",
            help="Edit notes associated to the document",
            action="store_true"
        )

        self.parser.add_argument(
            "--all",
            help="Edit all matching documents",
            action="store_true"
        )

    def main(self):

        documents = self.get_db().query(self.args.search)
        if not self.args.all:
            document = self.pick(documents)
            documents = [document] if document else []

        if len(documents) == 0:
            return 0

        for document in documents:
            if self.args.notes:
                self.logger.debug("Editing notes")
                if not document.has("notes"):
                    self.logger.warning(
                        "The document selected has no notes attached,"
                        " creating one..."
                    )
                    document["notes"] = papis.config.get("notes-name")
                    document.save()
                notesPath = os.path.join(
                    document.get_main_folder(),
                    document["notes"]
                )
                if not os.path.exists(notesPath):
                    self.logger.debug("Creating %s" % notesPath)
                    open(notesPath, "w+").close()
                papis.api.edit_file(notesPath)
            else:
                run(document)
