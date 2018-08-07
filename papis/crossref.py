from __future__ import unicode_literals
import logging
import re
from string import ascii_lowercase
import papis.config
import papis.utils
logger = logging.getLogger("crossref")
logger.debug("importing")

# CrossRef queries
#
# CrossRef documentation comes from here:
# http://labs.crossref.org/site/quick_and_dirty_api_guide.html
#
# You need a CrossRef API key.
#
CROSSREF_KEY = "fx.coudert@chimie-paristech.fr"
CROSSREF_KEY = "a.gallo@fkf.mpg.de"


def collapse_whitespace(s):
    """Removes whitespace from string and returns the result. Useful
    when whitespace causes errors (e.g. Bibtex)

    :param s: string
    :type s: str
    """
    logger.debug("Removing whitespace...")
    return s.replace(" ", "")


def crossref_data_to_papis_data(data):
    new_data = dict()
    if "author" in data.keys():
        authors = []
        for author in data["author"]:
            if "given" in author.keys() and "family" in author.keys():
                authors.append(
                    dict(given_name=author["given"], surname=author["family"])
                )
        new_data["author_list"] = authors
        new_data["author"] = ",".join(
            ["{a[given_name]} {a[surname]}".format(a=a) for a in authors]
        )
    if 'title' in data.keys():
        new_data["title"] = " ".join(data['title'])
    if 'doi' in data.keys():
        new_data["doi"] = data["DOI"]
    if 'DOI' in data.keys():
        new_data["doi"] = data["DOI"]
    if 'url' in data.keys():
        new_data["url"] = data["url"]
    if 'URL' in data.keys():
        new_data["url"] = data["URL"]
    return new_data


def get_data(query="", author="", title="", max_results=20):
    import habanero
    cr = habanero.Crossref()
    data = dict(
        query=query, query_author=author,
        query_title=title, limit=max_results
    )
    kwargs = {key: data[key] for key in data.keys() if data[key]}
    results = cr.works(sort='relevance', **kwargs)
    logger.debug("Retrieved {} documents".format(len(results)))
    return [
        crossref_data_to_papis_data(d) for d in results["message"]["items"]
    ]


def validate_doi(doi):
    """We check that the DOI can be resolved by official means.  If so, we
    return the resolved URL, otherwise, we return None (which means the DOI is
    invalid).

    :param doi: Doi identificator
    :type  doi: str
    """
    from urllib.request import urlopen
    handle_url = "https://doi.org/" + doi
    logger.debug('handle url %s' % handle_url)
    try:
        handle = urlopen(handle_url)
    except:  # What exception are we catching?
        return None

    resolvedURL = handle.geturl()
    logger.debug('resolved url %s' % resolvedURL)
    if resolvedURL[0:16] == "https://doi.org/":
        return None
    else:
        return resolvedURL


def get_citation_info_from_results(container):
    """This function retrieves the citations from the container's answer

    :param container: xml information
    :returns: Dictionary with information to be added
    :rtype:  dict

    """
    citations_info = dict(citations=[])
    logger.debug("Getting citations..")

    for node in container.getElementsByTagName("citation"):
        citation = dict()
        # Some documents do not have a doi:
        doi_node = node.getElementsByTagName('doi')
        if len(doi_node) == 0:
            continue
        doi = doi_node[0].firstChild.data
        citation['doi'] = doi
        citations_info['citations'].append(citation)

    return citations_info


def get_author_info_from_results(container):
    """This function retrieves the authors from the container answer

    :param container: xml information
    :returns: Dictionary with information to be added
    :rtype:  dict

    """
    logger.debug("Getting authors..")
    authors_info = dict(author_list=[], author=None)

    for node in container.getElementsByTagName("person_name"):
        author = dict()
        surname = node.getElementsByTagName('surname')[0].firstChild.data
        given_name = node.getElementsByTagName('given_name')[0].firstChild.data
        author['surname'] = surname
        author['given_name'] = given_name
        authors_info['author_list'].append(author)

    authors_info['author'] = papis.config.get('multiple-authors-separator')\
        .join([
            papis.config.get("multiple-authors-format").format(au=author)
            for author in authors_info['author_list']
        ])

    return authors_info


def get_cross_ref(doi):
    """Get the XML from CrossRef
    """
    global CROSSREF_KEY
    global logger
    import xml.dom.minidom
    from urllib.parse import urlencode
    from urllib.request import urlopen, Request
    params = urlencode({
        "id": "doi:" + doi,
        "noredirect": "true",
        "pid": CROSSREF_KEY,
        "format": "unixref"
    })
    req_url = "http://www.crossref.org/openurl/?" + params
    url = Request(
        req_url,
        headers={
            'User-Agent': papis.config.get('user-agent')
        }
    )
    doc = urlopen(url).read()
    logger.debug("Request url: %s" % req_url)

    # Parse it
    doc = xml.dom.minidom.parseString(doc)
    records = doc.getElementsByTagName("journal")

    # No results. Is it a valid DOI?
    if len(records) == 0:
        res = validate_doi(doi)
        if res is None:
            raise Exception("Invalid DOI")
        else:
            raise Exception("Can't locate metadata")

    if (len(records) != 1):
        raise Exception("CrossRef returned more than one record")

    record = records[0]

    # helper functions
    def find_item_named(container, name):
        obj_list = container.getElementsByTagName(name)
        if (len(obj_list) == 0):
            return None
        else:
            return obj_list[0]

    def data(node):
        if node is None:
            return None
        else:
            return node.firstChild.data

    res = dict()

    # JOURNAL INFO
    journal = find_item_named(record, "journal_metadata")
    if journal:
        res["full_journal_title"] = data(
            find_item_named(journal, "full_title"))
        res["abbrev_journal_title"] = data(
            find_item_named(journal, "abbrev_title"))

    # VOLUME INFO
    issue = find_item_named(record, "journal_issue")
    res["issue"] = data(find_item_named(issue, "issue"))
    res["volume"] = data(find_item_named(issue, "volume"))
    res["year"] = data(find_item_named(issue, "year"))

    # URLS INFO
    doi_resources = record\
        .getElementsByTagName('doi_data')[0]\
        .getElementsByTagName('item')
    for resource in doi_resources:
        if resource.hasAttribute('crawler'):
            key = papis.config.get('doc-url-key-name')
        else:
            key = 'url'
        if key:
            res[key] = resource.getElementsByTagName('resource')[0]\
                .firstChild.data
        key = False

    # OTHER INFO
    other = find_item_named(record, "journal_article")
    res["title"] = data(find_item_named(other, "title")).replace("\n", "")
    res["first_page"] = data(find_item_named(other, "first_page"))
    res["last_page"] = data(find_item_named(other, "last_page"))
    if res["first_page"] is not None and res["last_page"] is not None:
        res['pages'] = res["first_page"] + "--" + res["last_page"]
    else:
        del res['first_page']
        del res['last_page']
    res["doi"] = data(find_item_named(other, "doi"))
    if res["year"] is None:
        res["year"] = data(find_item_named(other, "year"))

    # AUTHOR INFO
    res.update(get_author_info_from_results(record))

    # CITATION INFO
    res.update(get_citation_info_from_results(record))

    # REFERENCE BUILDING
    res['ref'] = collapse_whitespace(
        papis.utils.format_doc(papis.config.get("ref-format"), res)
    )

    # Check if reference field with the same tag already exists
    documents = papis.api.get_documents_in_lib(
        'papers',
    )
    ref_list = [doc['ref'] for doc in documents]

    if res['ref'] in ref_list:
        m = papis.utils.create_identifier(ascii_lowercase)
        while True:
            append_string = next(m)
            # Check if appended tag already exists
            if str(res['ref'] + '{}').format(append_string) in ref_list:
                continue            # It does? Keep checking.
            # If it doesn't...
            else:
                # ...make this the new ref tag value
                res['ref'] = str(res['ref'] + '{}').format(append_string)
                break

    # Journal checking
    # If the key journal does not exist check for abbrev_journal_title
    # and full_journal_title and set it then to one of them
    if 'journal' not in res.keys():
        for key in ['abbrev_journal_title', 'full_journal_title']:
            if key in res.keys():
                res['journal'] = res[key]

    return res


def get_clean_doi(doi):
    """Check if doi is actually a url and in that case just get
    the exact doi.

    :doi: String containing a doi
    :returns: The pure doi

    >>> get_clean_doi('http://dx.doi.org/10.1063%2F1.881498')
    '10.1063/1.881498'
    >>> get_clean_doi('http://dx.doi.org/10.1063/1.881498')
    '10.1063/1.881498'
    >>> get_clean_doi('10.1063%2F1.881498')
    '10.1063/1.881498'
    >>> get_clean_doi('10.1063/1.881498')
    '10.1063/1.881498'
    >>> get_clean_doi(\
            'http://physicstoday.scitation.org/doi/10.1063/1.uniau12/abstract'\
        )
    '10.1063/1.uniau12'
    >>> get_clean_doi(\
            'http://scitation.org/doi/10.1063/1.uniau12/abstract?as=234' \
        )
    '10.1063/1.uniau12'
    >>> get_clean_doi('http://physicstoday.scitation.org/doi/10.1063/1.881498')
    '10.1063/1.881498'
    >>> get_clean_doi(\
            'https://doi.org/10.1093/analys/anw053' \
        )
    '10.1093/analys/anw053'
    >>> get_clean_doi(\
            'http://physicstoday.scitation.org/doi/10.1063/1.881498?asdfwer' \
        )
    '10.1063/1.881498'
    """
    mdoi = re.match(
        r'^([^?/&%$^]+)(/|%2F)([^?&%$^]+).*',
        re.sub(
            r'.*doi(.org)?/', '',
            doi.replace("/abstract", "")
        )
    )
    if mdoi:
        return mdoi.group(1) + '/' + mdoi.group(3)
    else:
        return None


def doi_to_data(doi):
    """Search through crossref and get a dictionary containing the data

    :param doi: Doi identificator
    :type  doi: str
    :returns: Dictionary containing the data

    """
    global logger
    doi = get_clean_doi(doi)
    try:
        data = get_cross_ref(doi)
    except Exception as e:
        logger.error(
            "Couldn't resolve DOI '" + doi +
            "' through CrossRef: " + str(e) + "\n"
        )
        return dict()
    else:
        return data
