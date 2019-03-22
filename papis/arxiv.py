"""The following table lists the field prefixes for all the fields
 that can be searched.

 Table:          search_query field prefixes
============================================
 prefix          explanation
--------------------------------------------
 ti              Title
 au              Author
 abs             Abstract
 co              Comment
 jr              Journal Reference
 cat             Subject Category
 rn              Report Number
 id              Id (use id_list instead)
 all             All of the above
"""
import bs4
import logging
import urllib.request  # urlopen, Request
import urllib.parse  # import urlencode
import papis.config
import re


logger = logging.getLogger('arxiv')


def get_data(
    query="",
    author="",
    title="",
    abstract="",
    comment="",
    journal="",
    report_number="",
    category="",
    id_list="",
    page=0,
    max_results=30
):
    dict_params = {
        "all": query,
        "ti": title,
        "au": author,
        "cat": category,
        "abs": abstract,
        "co": comment,
        "jr": journal,
        "id_list": id_list,
        "rn": report_number
    }
    result = []
    clean_params = {x: dict_params[x] for x in dict_params if dict_params[x]}
    search_query = '+AND+'.join(
        [key+':'+str(clean_params[key]) for key in clean_params]
    )
    logger.debug("query = " + search_query)
    params = urllib.parse.urlencode(
        {
            'search_query': search_query,
            'start': page,
            'max_results': max_results
        }
    )
    main_url = "http://arxiv.org/api/query?"
    req_url = main_url + params
    logger.debug("url = " + req_url)
    url = urllib.request.Request(
        req_url,
        headers={
            'User-Agent': papis.config.get('user-agent')
        }
    )
    xmldoc = urllib.request.urlopen(url).read()
    soup = bs4.BeautifulSoup(xmldoc, 'html.parser')

    entries = soup.find_all("entry")
    for entry in entries:
        data = dict()
        data["abstract"] = entry.find("summary").get_text().replace(
            "\n", " "
        )
        data["url"] = entry.find("id").get_text()
        data["published"] = entry.find("published").get_text()
        data["year"] = data.get("published")[0:4]
        data["title"] = entry.find("title").get_text().replace("\n", " ")
        data["author"] = ", ".join(
            [
                author.get_text().replace("\n", "")
                for author in entry.find_all("author")
            ]
        )
        result.append(data)
    return result


def pdf_to_arxivid(filepath):
    """Try to get arxivid from a filepath, it looks for a regex in the binary
    data and returns the first arxivid found, in the hopes that this arxivid
    is the correct one.

    :param filepath: Path to the pdf file
    :type  filepath: str
    :returns: arxivid or None
    :rtype:  str or None
    """
    regex = re.compile(r'arxiv.org/([^)]+)', re.I)
    arxivid = None
    with open(filepath, 'rb') as fd:
        for line in fd:
            arxivid = find_arxivid_in_text(line.decode('ascii', errors='ignore'))
            if arxivid:
                break
    return arxivid


def find_arxivid_in_text(text):
    """
    Try to find a arxivid in a text
    """
    forbidden_arxivid_characters = r'"\(\)\s%$^\'<>@,;:#?&'
    # Sometimes it is in the javascript defined
    regex = re.compile(
        r'arxiv(.org/)?'
        r'(abs|pdf)?'
        r'\s*(=|:|/|\()\s*'
        r'("|\')?'
        r'(?P<arxivid>[^{fc}]+)'
        r'("|\'|\))?'
        .format(
            fc=forbidden_arxivid_characters
        ), re.I
    )
    miter = regex.finditer(text)
    try:
        m = next(miter)
        if m:
            arxivid = m.group('arxivid')
            return arxivid
    except StopIteration:
        pass
    return None
