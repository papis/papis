import papis
import papis.utils
import papis.yaml
import logging
import papis.doi
import papis.arxiv
import papis.document
import papis.cli
import papis.yaml
import os.path
from stevedore import extension

logger = logging.getLogger('importer')

class Context:
    files = []
    data = dict()

class Importer:
    """This is the base class for every importer"""

    def __init__(self, uri="", name="", ctx=Context()):
        """
        :param uri: uri
        :type  uri: str
        :param name: Name of the importer
        :type  name: str
        """
        assert(isinstance(uri, str))
        assert(isinstance(name, str))
        assert(isinstance(ctx, Context))
        self.uri = uri
        self.name = name or os.path.basename(__file__)
        self.logger = logging.getLogger("importer:{0}".format(self.name))
        self.ctx = ctx

    @classmethod
    def match(uri):
        """This method should be called to know if a given uri matches
        the importer or not.

        For example, a valid match for archive would be:
        .. code:: python

            return re.match(r".*arxiv.org.*", uri)

        it will return something that is true if it matches and something
        falsely otherwise.

        :param uri: uri where the document should be retrieved from.
        :type  uri: str
        """
        raise NotImplementedError(
            "Matching uri not implemented for this downloader"
        )

    def fetch(self):
        """
        can return a dict to update the document with
        """
        raise NotImplementedError()

    def __str__(self):
        return 'Importer({0}, uri={1})'.format(self.name, self.uri)


class BibtexImporter(Importer):
    name = "bibtex"
    def fetch(self, from_bibtex):
        """
        :param from_bibtex: Filepath where to find a file containing bibtex info.
        :type  from_bibtex: str
        """
        logger.info("Reading bibtex input file = %s" % from_bibtex)
        bib_data = papis.bibtex.bibtex_to_dict(from_bibtex)
        if len(bib_data) > 1:
            logger.warning(
                'Your bibtex file contains more than one entry,'
                ' I will be taking the first entry'
            )
        if bib_data:
            return bib_data[0]

    def matches(res):
        # return os.path.exist
        return papis.utils.get_document_extension(res) == 'bib'


class PdfImporter(Importer):
    def matches(res):
        return papis.utils.get_document_extension(res) == 'pdf'

    def fetch(from_yaml):
        # logger.info("Trying to parse doi from file {0}".format(files[0]))
        doi = papis.doi.pdf_to_doi(files[0])
        if doi:
            logger.info("Parsed doi {0}".format(doi))
            logger.warning("There is no guarantee that this doi is the one")
        # if (doi and
        #         not batch and
        #         confirm and
        #         papis.utils.confirm(
        #             'Do you want to use the doi {0}'.format(doi)
        #         )):
        #     from_doi = doi
    # TODO move into its own Arxiv importer ?
    #     arxivid = papis.arxiv.pdf_to_arxivid(files[0])
    #     if arxivid:
    #         logger.info("Parsed arxivid {0}".format(arxivid))
    #         logger.warning(
    #             "There is no guarantee that this arxivid is the one"
    #         )
    #     if (arxivid and
    #             not batch and
    #             confirm and
    #             papis.utils.confirm(
    #                 'Do you want to use the arxivid {0}'.format(arxivid)
    #             )):
    #         from_url = "https://arxiv.org/abs/{0}".format(arxivid)
        return papis.yaml.yaml_to_data(from_yaml)

class ArxivImporter(Importer):
    name = "arxiv"
    def matches(res):
        # or if the url is an arxiv one
        return papis.utils.get_document_extension(res) == 'pdf'

    def fetch(from_yaml):
        logger.info("Reading yaml input file = %s" % from_yaml)
        return papis.yaml.yaml_to_data(from_yaml)


class FromLibImporter(Importer):
    name = "from_lib"
    def matches(res):
        # if it's a folder/lib
        return res in papis.api.get_libraries()

    def fetch(self, from_lib):
        doc = papis.api.pick_doc(
            papis.api.get_all_documents_in_lib(from_lib)
        )
        if doc:
            from_folder = doc.get_main_folder()
            # TODO return several things

class FromFolder(Importer):
    name = "from_lib"
    def matches(res):
        # if it's a folder/lib
        return os.path.isdir()

    def fetch(self, from_lib):
        doc = papis.api.pick_doc(
            papis.api.get_all_documents_in_lib(from_lib)
        )
        if doc:
            from_folder = doc.get_main_folder()
            # TODO return several things


# class PMIDImporter(Importer):
#     name = "fromPMID"

#     def matches(res):
#         """
#         Ok if res is a number or an url that matches pubmed
#         """
#         try:
#             int(res)
#             return True
#         except ValueError:
#             pass

#         import re
#         hubmed_url = "http://pubmed.macropus.org/articles/"\
#                      "?format=text%%2Fbibtex&id="
#         if re.match(hubmed_url, res):
#             return True
#         return False


#     def fetch(self, from_pmid):

#         logger.info("Using PMID %s via HubMed" % from_pmid)
#         hubmed_url = "http://pubmed.macropus.org/articles/"\
#                      "?format=text%%2Fbibtex&id=%s" % from_pmid
#         bibtex_data = papis.downloaders.utils.get_downloader(
#             hubmed_url,
#             "get"
#         ).get_document_data().decode("utf-8")
#         bibtex_data = papis.bibtex.bibtex_to_dict(bibtex_data)
#         if len(bibtex_data):
#             data.update(bibtex_data[0])
#             if "doi" in data and not from_doi:
#                 from_doi = data["doi"]
#             return data
#         else:
#             logger.error("PMID %s not found or invalid" % from_pmid)


# class CrossrefImporter(Importer):
#     name = "crossref"
#     def matches(res):
#         # if it's a folder/lib
#         return True

#     def fetch(self, from_crossref):
#         logger.info("Querying crossref.org")
#         docs = [
#             papis.document.from_data(d)
#             for d in papis.crossref.get_data(query=from_crossref)
#         ]
#         if docs:
#             logger.info("got {0} matches, picking...".format(len(docs)))
#             doc = papis.api.pick_doc(docs) if not batch else docs[0]
#             if doc and not from_doi and doc.has('doi'):
#                 from_doi = doc['doi']

# class DOIImporter(Importer):
#     name = "crossref"
#     def matches(res):
#         # if it's a folder/lib
#         return True
#     def fetch(self, from_lib):

#         logger.info("using doi {0}".format(from_doi))
#         doidata = papis.crossref.get_data(dois=[from_doi])
#         if doidata:
#             data.update(doidata[0])
#         if (len(files) == 0 and
#                 papis.config.get('doc-url-key-name') in data.keys()):

#             doc_url = data[papis.config.get('doc-url-key-name')]
#             logger.info(
#                 'You did not provide any files, but I found a possible '
#                 'url where the file might be'
#             )
#             logger.info(
#                 'I am trying to download the document from %s' % doc_url
#             )
#             down = papis.downloaders.utils.get_downloader(doc_url, 'get')
#             assert(down is not None)
#             tmp_filepath = tempfile.mktemp()
#             logger.debug("Saving in %s" % tmp_filepath)

#             with builtins.open(tmp_filepath, 'wb+') as fd:
#                 fd.write(down.get_document_data())

#             logger.info('Opening the file')
#             papis.api.open_file(tmp_filepath)
#             if papis.utils.confirm('Do you want to use this file?'):
#                 files.append(tmp_filepath)

def stevedore_error_handler(manager, entrypoint, exception):
    logger.error("Error while loading entrypoint [%s]" % entrypoint)
    logger.error(exception)


import_mgr = None


def _create_import_mgr():
    global import_mgr
    if import_mgr:
        return
    import_mgr = extension.ExtensionManager(
        namespace='papis.importer',
        invoke_on_load=True,
        verify_requirements=True,
        invoke_args=(),
        # invoke_kwds
        propagate_map_exceptions=True,
        on_load_failure_callback=stevedore_error_handler
    )


def available_importers():
    global import_mgr
    _create_import_mgr()
    return import_mgr.entry_points_names()


def get_import_mgr():
    global import_mgr
    _create_import_mgr()
    return import_mgr
