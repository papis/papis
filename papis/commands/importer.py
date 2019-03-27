import papis
import papis.utils
import papis.yaml
import logging
import papis.doi
import papis.arxiv
import papis.document
import papis.downloaders.utils
import papis.cli
import papis.yaml

logger = logging.getLogger('importer')

class Importer:
    name = "unset"
    def __init__(self,):
        pass


    @staticmethod
    def matches(param) -> bool:
        """
        Check if this is a candidate for this importer

        """
        raise NotImplementedError()


    # TODO pass other parameters such as confirm etc ?
    def fetch(resource):
        """
        can return a dict to update the document with
        """
        raise NotImplementedError()



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

class YamlImporter(Importer):

    def fetch(from_yaml):
        logger.info("Reading yaml input file = %s" % from_yaml)
        return papis.yaml.yaml_to_data(from_yaml)

class FromlibImporter(Importer):
    name = "from_lib"
    def matches(res):
        # if it's a folder/lib
        return True

    def fetch(self, from_lib):
        doc = papis.api.pick_doc(
            papis.api.get_all_documents_in_lib(from_lib)
        )
        if doc:
            from_folder = doc.get_main_folder()
            # TODO return several things


class FromlibImporter(Importer):
    name = "fromPMID"

    def matches(res):
        """
        Ok if res is a number or an url that matches pubmed
        """
        try:
            int(res)
            return True
        except ValueError:
            pass

        import re
        hubmed_url = "http://pubmed.macropus.org/articles/"\
                     "?format=text%%2Fbibtex&id="
        if re.match(hubmed_url, res):
            return True
        return False


    def fetch(self, from_pmid):

        logger.info("Using PMID %s via HubMed" % from_pmid)
        hubmed_url = "http://pubmed.macropus.org/articles/"\
                     "?format=text%%2Fbibtex&id=%s" % from_pmid
        bibtex_data = papis.downloaders.utils.get_downloader(
            hubmed_url,
            "get"
        ).get_document_data().decode("utf-8")
        bibtex_data = papis.bibtex.bibtex_to_dict(bibtex_data)
        if len(bibtex_data):
            data.update(bibtex_data[0])
            if "doi" in data and not from_doi:
                from_doi = data["doi"]
            return data
        else:
            logger.error("PMID %s not found or invalid" % from_pmid)

