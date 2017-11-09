"""
The add command is one of the central commands of the papis command line
interface. It is a very versatile command with a fair amount of options.

Examples
^^^^^^^^

    - Add a document located in ``~/Documents/interesting.pdf``
      and name the folder where it will be stored in the database
      ``interesting-paper-2021``

    .. code::

        papis add ~/Documents/interesting.pdf --name interesting-paper-2021

    - Add a paper that you have locally in a file and get the paper
      information through its ``doi`` identificator (in this case
      ``10.10763/1.3237134`` as an example):

    .. code::

        papis add ~/Documents/interesting.pdf --from-doi 10.10763/1.3237134

"""
import papis
import os
import sys
import re
import tempfile
import hashlib
import shutil
import string
import subprocess
import papis.api
import papis.utils
import papis.config
import papis.bibtex
import papis.document
import papis.downloaders.utils

class Command(papis.commands.Command):

    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "add",
            help="Add a document into a given library"
        )

        self.parser.add_argument(
            "document",
            help="Document file name",
            default=[],
            nargs="*",
            action="store"
        )

        self.parser.add_argument(
            "-d", "--dir",
            help="Subfolder in the library",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "-i", "--interactive",
            help="Do some of the actions interactively",
            action='store_false' if papis.config.get('add-interactive') \
                else 'store_true'
        )

        self.parser.add_argument(
            "--name",
            help="Name for the document's folder (papis format)",
            default=papis.config.get('add-name'),
            action="store"
        )

        self.parser.add_argument(
            "--title",
            help="Title for document",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--author",
            help="Author(s) for document",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--from-bibtex",
            help="Parse information from a bibtex file",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--from-yaml",
            help="Parse information from a yaml file",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--from-folder",
            help="Add document from folder being a valid papis document"
                 " (containing info.yaml)",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--from-url",
            help="Get document and information from a"
                "given url, a parser must be implemented",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "--from-doi",
            help="Doi to try to get information from",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--from-pmid",
            help="PMID to try to get information from",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--from-lib",
            help="Add document from another library",
            default="",
            action="store"
        )


        self.parser.add_argument(
            "--from-vcf",
            help="Get contact information from a vcard (.vcf) file",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--to",
            help="When --to is specified, the document will be added to the"
                "selected already existing document entry.",
            nargs="?",
            action="store"
        )

        self.parser.add_argument(
            "--confirm",
            help="Ask to confirm before adding to the collection",
            action='store_false' if papis.config.get('add-confirm') \
                else 'store_true'
        )

        self.parser.add_argument(
            "--open",
            help="Open file before adding document",
            action='store_false' if papis.config.get('add-open') \
                else 'store_true'
        )

        self.parser.add_argument(
            "--edit",
            help="Edit info file before adding document",
            action='store_false' if papis.config.get('add-edit') \
                else 'store_true'
        )

        self.parser.add_argument(
            "--commit",
            help="Commit document if library is a git repository",
            action="store_true"
        )

        self.parser.add_argument(
            "--no-document",
            help="Add entry without a document related to it",
            action="store_true"
        )

    def get_hash_folder(self, data, document_path):
        """Folder name where the document will be stored.

        :data: Data parsed for the actual document
        :document_path: Path of the document

        """
        author = "-{:.20}".format(data["author"])\
                 if "author" in data.keys() else ""
        with open(document_path, "rb") as fd:
            md5 = hashlib.md5(fd.read(4096)).hexdigest()
        result = md5 + author
        result = papis.utils.clean_document_name(result)
        return result

    def get_document_extension(self, documentPath):
        """Get document extension

        :document_path: Path of the document
        :returns: Extension (string)

        """
        # TODO: mimetype based (mimetype, rifle, ranger-fm ...?)
        m = re.match(r"^(.*)\.([a-zA-Z0-9]*)$", os.path.basename(documentPath))
        extension = m.group(2) if m else "txt"
        self.logger.debug("[ext] = %s" % extension)
        return extension

    def get_meta_data(self, key, document_path):
        # TODO: Consistent a general way to get metadata from documents.
        # TODO: pdfminer does not work very well
        self.logger.debug("Retrieving %s meta data" % key)
        extension = self.get_document_extension(document_path)
        return None

    def get_default_title(self, data, document_path):
        if "title" in data.keys(): return data["title"]
        extension = self.get_document_extension(document_path)
        title = self.get_meta_data("title", document_path)
        if not title:
            title = os.path.basename(document_path)\
                            .replace("."+extension, "")\
                            .replace("_", " ")\
                            .replace("-", " ")
            if self.get_args().interactive:
                title = papis.utils.input(
                    'Title?', title
                )
        return title

    def get_default_author(self, data, document_path):
        if "author" in data.keys(): return data["author"]
        author = self.get_meta_data("author", document_path)
        if not author:
            author = "Unknown"
            if self.get_args().interactive:
                author = papis.utils.input(
                    'Author?', author
                )
        return author

    def init_contact_mode(self):
        """Initialize the contact mode
        """
        self.logger.debug("Initialising contact mode")
        self.args.document = [papis.utils.get_info_file_name()]
        self.args.from_yaml = papis.utils.get_info_file_name()
        if os.path.exists(self.args.document[0]):
            return True
        self.args.edit = True
        self.args.confirm = True
        template = papis.document.Document.get_vcf_template()
        with open(self.args.document[0], "w+") as fd:
            fd.write(template)

    def main(self):
        if papis.config.in_mode("contact"):
            self.init_contact_mode()
        lib_dir = os.path.expanduser(papis.config.get('dir'))
        data = dict()
        # The folder name of the new document that will be created
        out_folder_name = None
        # The real paths of the documents to be added
        in_documents_paths = self.args.document
        # The basenames of the documents to be added
        in_documents_names = []
        # The folder name of the temporary document to be created
        temp_dir = tempfile.mkdtemp("-"+self.args.lib)

        if self.args.from_lib:
            doc = self.pick(
                papis.api.get_documents_in_lib(self.get_args().from_lib)
            )
            if doc:
                self.args.from_folder = doc.get_main_folder()

        if self.args.from_folder:
            original_document = papis.document.Document(self.args.from_folder)
            self.args.from_yaml = original_document.get_info_file()
            in_documents_paths = original_document.get_files()

        if self.args.from_url:
            url_data = papis.downloaders.utils.get(self.args.from_url)
            data.update(url_data["data"])
            in_documents_paths.extend(url_data["documents_paths"])
            # If no data was retrieved and doi was found, try to get
            # information with the document's doi
            if not data and url_data["doi"] is not None and\
                not self.args.from_doi:
                self.logger.warning(
                    "I could not get any data from %s" % self.args.from_url
                )
                self.args.from_doi = url_data["doi"]

        if self.args.from_bibtex:
            bib_data = papis.bibtex.bibtex_to_dict(self.args.from_bibtex)
            if len(bib_data) > 1:
                self.logger.warning(
                    'Your bibtex file contains more than one entry,'
                    ' I will be taking the first entry'
                )
            data.update(bib_data[0])

        if self.args.from_pmid:
            self.logger.debug(
                "I'll try using PMID %s via HubMed" % self.args.from_pmid
            )
            hubmed_url = "http://pubmed.macropus.org/articles/"\
                         "?format=text%%2Fbibtex&id=%s" % self.args.from_pmid
            bibtex_data = papis.downloaders.utils.get_downloader(
                hubmed_url,
                "get"
            ).get_document_data().decode("utf-8")
            bibtex_data = papis.bibtex.bibtex_to_dict(bibtex_data)
            if len(bibtex_data):
                data.update(bibtex_data[0])
                if "doi" in data and not self.args.from_doi:
                    self.args.from_doi = data["doi"]
            else:
                self.logger.error(
                    "PMID %s not found or invalid" % self.args.from_pmid
                )

        if self.args.from_doi:
            self.logger.debug("I'll try using doi %s" % self.args.from_doi)
            data.update(papis.utils.doi_to_data(self.args.from_doi))
            if len(self.get_args().document) == 0 and \
                    papis.config.get('doc-url-key-name') in data.keys():
                doc_url = data[papis.config.get('doc-url-key-name')]
                self.logger.info(
                    'I am trying to download the document from %s' % doc_url
                )
                down = papis.downloaders.utils.get_downloader(
                    doc_url,
                    'get'
                )
                file_name = tempfile.mktemp()
                with open(file_name, 'wb+') as fd:
                    fd.write(down.get_document_data())
                self.logger.info('Opening the file')
                papis.api.open_file(file_name)
                if papis.utils.confirm('Do you want to use this file?'):
                    self.args.document.append(file_name)

        if self.args.from_yaml:
            self.logger.debug("Yaml input file = %s" % self.args.from_yaml)
            data.update(papis.utils.yaml_to_data(self.args.from_yaml))

        if self.args.from_vcf:
            data.update(papis.utils.vcf_to_data(self.args.from_vcf))
        in_documents_names = [
            papis.utils.clean_document_name(doc_path)
            for doc_path in in_documents_paths
        ]

        # Decide if we are adding the documents to an already existing document
        # or it is a new document
        if self.args.to:
            self.logger.debug(
                "Searching for the document where to add the files"
            )
            documents = papis.api.get_documents_in_dir(
                lib_dir,
                self.args.to
            )
            document = self.pick(documents)
            if not document: return 0
            document.update(
                data,
                interactive=self.args.interactive
            )
            document.save()
            data = document.to_dict()
            in_documents_paths = document.get_files() + in_documents_paths
            data["files"] = [os.path.basename(f) for f in in_documents_paths]
            # set out folder name the folder of the found document
            out_folder_name = document.get_main_folder_name()
            out_folder_path = document.get_main_folder()
        else:
            document = papis.document.Document(temp_dir)
            if not papis.config.in_mode("contact"):
                if len(in_documents_paths) == 0:
                    if not self.get_args().no_document:
                        self.logger.error("No documents to be added")
                        return 1
                    else:
                        in_documents_paths = [document.get_info_file()]
                        # We need the names to add them in the file field
                        # in the info file
                        in_documents_names = [papis.utils.get_info_file_name()]
                        # Save document to create the info file
                        document.update(
                            data, force=True, interactive=self.args.interactive
                        )
                        document.save()
                data["title"] = self.args.title or self.get_default_title(
                    data,
                    in_documents_paths[0]
                )
                data["author"] = self.args.author or self.get_default_author(
                    data,
                    in_documents_paths[0]
                )
                self.logger.debug("Author = % s" % data["author"])
                self.logger.debug("Title = % s" % data["title"])

            if not self.args.name:
                self.logger.debug("Getting an automatic name")
                out_folder_name = self.get_hash_folder(
                    data,
                    in_documents_paths[0]
                )
            else:
                temp_doc = papis.document.Document(data=data)
                out_folder_name = papis.utils.format_doc(
                    self.args.name,
                    temp_doc
                )
                out_folder_name = papis.utils.clean_document_name(
                    out_folder_name
                )
                del temp_doc
            if len(out_folder_name) == 0:
                self.logger.error('The output folder name is empty')
                return 1

            data["files"] = in_documents_names
            out_folder_path = os.path.join(
                lib_dir, self.args.dir,  out_folder_name
            )

        self.logger.debug("Folder name = % s" % out_folder_name)
        self.logger.debug("Folder path = % s" % out_folder_path)
        self.logger.debug("File(s)     = % s" % in_documents_paths)

        # Create folders if they do not exists.
        if not os.path.isdir(temp_dir):
            self.logger.debug("Creating directory '%s'" % temp_dir)
            os.makedirs(temp_dir, mode=papis.config.getint('dir-umask'))

        # Check if the user wants to edit before submitting the doc
        # to the library
        if self.args.edit:
            document.update(
                data, force=True, interactive=self.args.interactive
            )
            document.save()
            self.logger.debug("Editing file before adding it")
            papis.api.edit_file(document.get_info_file())
            self.logger.debug("Loading the changes made by editing")
            document.load()
            data = document.to_dict()

        # First prepare everything in the temporary directory
        for i in range(min(len(in_documents_paths), len(data["files"]))):
            in_doc_name = data["files"][i]
            in_file_path = in_documents_paths[i]
            assert(os.path.exists(in_file_path))
            endDocumentPath = os.path.join(
                document.get_main_folder(),
                in_doc_name
            )
            if os.path.exists(endDocumentPath):
                self.logger.debug(
                    "%s already exists, ignoring..." % endDocumentPath
                )
                continue
            if not self.args.no_document:
                self.logger.debug(
                    "[CP] '%s' to '%s'" %
                    (in_file_path, endDocumentPath)
                )
                shutil.copy(in_file_path, endDocumentPath)

        # Duplication checking
        self.logger.debug("Check if the added document is already existing")
        found_document = papis.utils.locate_document(
            document, papis.api.get_documents_in_lib(papis.api.get_lib())
        )
        if found_document is not None:
            self.logger.warning("DUPLICATION WARNING")
            self.logger.warning(
                "This document seems to be already in your libray: \n\n" +
                found_document.dump()
            )
            self.logger.warning(
                "Use the update command if you just want to update the info."
            )
            self.args.confirm = True

        document.update(data, force=True)
        if self.get_args().open:
            for d_path in in_documents_paths:
                papis.api.open_file(d_path)
        if self.args.confirm:
            if not papis.utils.confirm('Really add?'):
                return 0
        document.save()
        if self.args.to:
            return 0
        self.logger.debug(
            "[MV] '%s' to '%s'" %
            (document.get_main_folder(), out_folder_path)
        )
        shutil.move(document.get_main_folder(), out_folder_path)
        # Let us chmod it because it might come from a temp folder
        # and temp folders are per default 0o600
        os.chmod(out_folder_path, papis.config.getint('dir-umask'))
        papis.api.clear_lib_cache()
        if self.args.commit and papis.utils.lib_is_git_repo(self.args.lib):
            subprocess.call(["git", "-C", out_folder_path, "add", "."])
            subprocess.call(
                ["git", "-C", out_folder_path, "commit", "-m", "Add document"]
            )
