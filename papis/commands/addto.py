from string import ascii_lowercase
import os
import shutil
import papis.api
from papis.api import status
import papis.utils
import papis.document
import papis.config
import papis.commands.add
import logging


def run(document, filepaths):
    logger = logging.getLogger('addto')
    g = papis.utils.create_identifier(ascii_lowercase)
    string_append = ''
    for i in range(len(document.get_files())):
        string_append = next(g)

    new_file_list = []
    for i in range(len(filepaths)):
        in_file_path = filepaths[i]

        if not os.path.exists(in_file_path):
            raise Exception("{} not found".format(in_file_path))

        # Rename the file in the staging area
        new_filename = papis.utils.clean_document_name(
            papis.commands.add.get_file_name(
                papis.document.to_dict(document),
                in_file_path,
                suffix=string_append
            )
        )
        new_file_list.append(new_filename)

        endDocumentPath = os.path.join(
            document.get_main_folder(),
            new_filename
        )
        string_append = next(g)

        # Check if the absolute file path is > 255 characters
        if len(os.path.abspath(endDocumentPath)) >= 255:
            logger.warning(
                'Length of absolute path is > 255 characters. '
                'This may cause some issues with some pdf viewers'
            )

        if os.path.exists(endDocumentPath):
            logger.warning(
                "%s already exists, ignoring..." % endDocumentPath
            )
            continue
        logger.debug(
            "[CP] '%s' to '%s'" %
            (in_file_path, endDocumentPath)
        )
        shutil.copy(in_file_path, endDocumentPath)

    document['files'] = document.get_files() + new_file_list
    document.save()
    return status.success


class Command(papis.commands.Command):

    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "addto",
            help="Add files to an existing document"
        )

        self.add_search_argument()

        self.parser.add_argument(
            "-f", "--files",
            help="File fullpaths to documents",
            default=[],
            nargs="*",
            action="store"
        )

        self.parser.add_argument(
            "--file-name",
            help="File name for the document (papis format)",
            action="store",
            default=None
        )

    def main(self):
        db = papis.database.get(self.args.lib)
        documents = db.query(self.args.search)
        document = papis.api.pick_doc(documents)
        if not document:
            return status.file_not_found

        if self.args.file_name is not None:  # Use args if set
            papis.config.set("file-name", self.args.file_name)

        return run(document, self.args.files)
