import re
import logging

logger = logging.getLogger("doi")


def pdf_to_doi(filepath):
    """Try to get doi from a filepath, it looks for a regex in the binary
    data and returns the first doi found, in the hopes that this doi
    is the correct one.

    :param filepath: Path to the pdf file
    :type  filepath: str
    :returns: DOI or None
    :rtype:  str or None
    """
    regex = re.compile(r'doi.org/([^)]+)', re.I)
    doi = None
    with open(filepath, 'rb') as fd:
        for line in fd:
            doi = find_doi_in_text(line.decode('ascii', errors='ignore'))
            if doi:
                break
    return doi


def validate_doi(doi):
    """We check that the DOI can be resolved by official means.  If so, we
    return the resolved URL, otherwise, we return None (which means the DOI is
    invalid).

    http://www.doi.org/factsheets/DOIProxy.html

    :param doi: Doi identificator
    :type  doi: str

    :raises ValueError: Whenever the doi is not valid
    """
    from urllib.error import HTTPError
    import urllib.request
    import urllib.parse
    import json
    url = "https://doi.org/api/handles/{doi}".format(doi=doi)
    logger.debug('handle url %s' % url)
    request = urllib.request.Request(url)

    try:
        result = json.loads(urllib.request.urlopen(request).read().decode())
    except HTTPError:
        raise ValueError('HTTP 404: DOI not found')

    response_code = int(result["responseCode"])
    if response_code in [1, 200]:
        # HTTP 200 all ok
        logger.debug('HTTP 200: valid doi')
    elif response_code == 2:
        raise ValueError('HTTP 500: Interal DOI server error')
    elif response_code == 100:
        raise ValueError('HTTP 404: DOI not found')
    else:
        raise ValueError('Something unexpected happened')


def get_clean_doi(doi):
    """Check if doi is actually a url and in that case just get
    the exact doi.

    :doi: String containing a doi
    :returns: The pure doi
    """
    doi = find_doi_in_text(doi)
    if not doi:
        return doi
    else:
        return re.sub(r'(/abstract)', '', doi)


def find_doi_in_text(text):
    """
    Try to find a doi in a text
    """
    text = re.sub(r'%2F', '/', text)
    text = re.sub(r'\)>', ' ', text)
    forbidden_doi_characters = r'"\s%$^\'<>@,#?&'
    # Sometimes it is in the javascript defined
    var_doi = re.compile(
        r'doi(.org)?'
        r'\s*(=|:|/)\s*'
        r'("|\')?'
        r'(?P<doi>[^{fc}]+)'
        r'("|\')?'
        .format(
            fc=forbidden_doi_characters
        ), re.I
    )

    for regex in [var_doi]:
        miter = regex.finditer(text)
        try:
            m = next(miter)
            if m:
                doi = m.group('doi')
                return doi
        except StopIteration:
            pass
    return None
