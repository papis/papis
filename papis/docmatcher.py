import papis.config
import logging


class DocMatcher(object):
    """This class implements the mini query language for papis.
    All its methods are static, it could be also implemented as a separate
    module.

    The static methods are to be used as follows:
    First the search string has to be set,
        DocMatcher.set_search(search_string)
    and then the parse method should be called in order to decypher the
    search_string,
        DocMatcher.parse()
    Now the DocMatcher is ready to match documents with the input query
    via the `return_if_match` method, which is used to parallelize the
    matching.
    """
    search = ""
    parsed_search = None
    doc_format = '{' + papis.config.get('format-doc-name') + '[DOC_KEY]}'
    logger = logging.getLogger('DocMatcher')
    matcher = None

    @classmethod
    def return_if_match(cls, doc):
        """Use the attribute `cls.parsed_search` to match the `doc` document
        to the previously parsed query.
        :param doc: Papis document to match against.
        :type  doc: papis.document.Document
        :returns: True if it matches, False if some query requirement does
            not match.

        >>> import papis.document
        >>> from papis.database.cache import match_document
        >>> doc = papis.document.from_data(dict(title='einstein'))
        >>> DocMatcher.set_matcher(match_document)
        >>> DocMatcher.parse('einste')
        ([(['einste'], {})], {})
        >>> DocMatcher.return_if_match(doc) is not None
        True
        >>> DocMatcher.parse('heisenberg')
        ([(['heisenberg'], {})], {})
        >>> DocMatcher.return_if_match(doc) is not None
        False
        >>> DocMatcher.parse('title = ein')
        ([(['title', '=', 'ein'], {})], {})
        >>> DocMatcher.return_if_match(doc) is not None
        True

        """
        match = None
        for parsed in cls.parsed_search:
            if len(parsed) == 1:
                search = parsed[0]
                sformat = None
            elif len(parsed) == 3:
                search = parsed[2]
                sformat = cls.doc_format.replace('DOC_KEY', parsed[0])
            match = doc if cls.matcher(doc, search, sformat) else None
            if not match:
                break
        return match

    @classmethod
    def set_search(cls, search):
        """
        >>> DocMatcher.set_search('author = Hummel')
        >>> DocMatcher.search
        'author = Hummel'
        """
        cls.search = search

    @classmethod
    def set_matcher(cls, matcher):
        """
        >>> from papis.database.cache import match_document
        >>> DocMatcher.set_matcher(match_document)
        """
        cls.matcher = matcher

    @classmethod
    def parse(cls, search=None):
        """Parse the main query text. This method will also set the
        class attribute `parsed_search` to the parsed query, and it will
        return it too.
        :param cls: The class object, since it is a static method
        :type  cls: object
        :param search: Search text string if a custom search string is to be
            used. False if the `cls.search` class attribute is to be used.
        :type  search: str
        :returns: Parsed query
        :rtype:  list
        >>> print(DocMatcher.parse('hello author = einstein'))
        [['hello'], ['author', '=', 'einstein']]
        >>> print(DocMatcher.parse(''))
        []
        >>> print(\
            DocMatcher.parse(\
                '"hello world whatever =" tags = \\\'hello ====\\\''))
        [['hello world whatever ='], ['tags', '=', 'hello ====']]
        >>> print(DocMatcher.parse('hello'))
        [['hello']]
        """
        if search is None:
            search = cls.search
        cls.parsed_search = parse_query(search)
        return cls.parsed_search


def parse_query(query_string):
    """
    >>> print(parse_query('hello   author = einstein'))
    [['hello'], ['author', '=', 'einstein']]
    """
    import pyparsing
    logger = logging.getLogger('query_parser')
    logger.debug('Parsing search')
    papis_key = pyparsing.Word(pyparsing.alphanums + '-')
    papis_value = pyparsing.QuotedString(
        quoteChar='"', escChar='\\', escQuote='\\'
    ) ^ pyparsing.QuotedString(
        quoteChar="'", escChar='\\', escQuote='\\'
    ) ^ papis_key
    equal = pyparsing.ZeroOrMore(" ") + \
        pyparsing.Literal('=') + \
        pyparsing.ZeroOrMore(" ")

    papis_query = pyparsing.ZeroOrMore(
        pyparsing.Group(
            pyparsing.ZeroOrMore(
                papis_key + equal
            ) + papis_value
        )
    )
    parsed = papis_query.parseString(query_string)
    logger.debug('Parsed query = %s' % parsed)
    return parsed
