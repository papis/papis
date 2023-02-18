from typing import Any, Callable, List, NamedTuple, Optional

import papis.config
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)

MATCHER_TYPE = Callable[
    [papis.document.Document, str, Optional[str], Optional[str]],
    Any
]

ParseResult = NamedTuple("ParseResult", [
    ("search", str),
    ("doc_key", Optional[str]),
    ])


class DocMatcher(object):
    """This class implements the mini query language for papis.
    All its methods are static, it could be also implemented as a separate
    module.

    The static methods are to be used as follows:
    First the search string has to be set::

        DocMatcher.set_search(search_string)

    and then the parse method should be called in order to decipher the
    *search_string*::

        DocMatcher.parse()

    Now the :class:`DocMatcher` is ready to match documents with the input
    query via the :meth:`DocMatcher.return_if_match` method, which is used to
    parallelize the matching.
    """

    search = ""  # type: str
    parsed_search = None  # type: List[ParseResult]
    matcher = None  # type: Optional[MATCHER_TYPE]
    match_format = papis.config.getstring("match-format")   # type: str

    @classmethod
    def return_if_match(
            cls,
            doc: papis.document.Document) -> Optional[papis.document.Document]:
        """Use the attribute `cls.parsed_search` to match the `doc` document
        to the previously parsed query.
        :param doc: Papis document to match against.

        >>> import papis.document
        >>> from papis.database.cache import match_document
        >>> doc = papis.document.from_data({'title': 'einstein'})
        >>> DocMatcher.set_matcher(match_document)
        >>> result = DocMatcher.parse('einste')
        >>> DocMatcher.return_if_match(doc) is not None
        True
        >>> result = DocMatcher.parse('heisenberg')
        >>> DocMatcher.return_if_match(doc) is not None
        False
        >>> result = DocMatcher.parse('title : ein')
        >>> DocMatcher.return_if_match(doc) is not None
        True
        """
        match = None
        if cls.parsed_search is None or cls.matcher is None:
            return match

        for p in cls.parsed_search:
            match = (
                doc if cls.matcher(doc, p.search, cls.match_format, p.doc_key)
                else None)

            if not match:
                break
        return match

    @classmethod
    def set_search(cls, search: str) -> None:
        """
        >>> DocMatcher.set_search('author = Hummel')
        >>> DocMatcher.search
        'author = Hummel'
        """
        cls.search = search

    @classmethod
    def set_matcher(cls, matcher: MATCHER_TYPE) -> None:
        """
        >>> from papis.database.cache import match_document
        >>> DocMatcher.set_matcher(match_document)
        """
        cls.matcher = matcher

    @classmethod
    def parse(cls, search: Optional[str] = None) -> List[ParseResult]:
        """Parse the main query text. This method will also set the
        class attribute `parsed_search` to the parsed query, and it will
        return it too.
        :param cls: The class object, since it is a static method
        :param search: Search text string if a custom search string is to be
            used. False if the `cls.search` class attribute is to be used.
        :returns: Parsed query

        >>> print(DocMatcher.parse('hello author : einstein'))
        [['hello'], ['author', ':', 'einstein']]
        >>> print(DocMatcher.parse(''))
        []
        >>> print(\
            DocMatcher.parse(\
                '"hello world whatever :" tags : \\\'hello ::::\\\''))
        [['hello world whatever :'], ['tags', ':', 'hello ::::']]
        >>> print(DocMatcher.parse('hello'))
        [['hello']]
        """
        if search is None:
            search = cls.search
        cls.parsed_search = parse_query(search)
        return cls.parsed_search


def parse_query(query_string: str) -> List[ParseResult]:
    import pyparsing
    logger.debug("Parsing query: '%s'", query_string)

    papis_key_word = pyparsing.Word(pyparsing.alphanums + "-._/")
    papis_value_word = pyparsing.Word(pyparsing.alphanums + "-._/()")

    papis_value = pyparsing.QuotedString(
        quoteChar='"', escChar="\\", escQuote="\\"
    ) ^ pyparsing.QuotedString(
        quoteChar="'", escChar="\\", escQuote="\\"
    ) ^ papis_value_word

    equal = (
        pyparsing.ZeroOrMore(pyparsing.Literal(" "))
        + pyparsing.Literal(":")
        + pyparsing.ZeroOrMore(pyparsing.Literal(" "))
    )

    papis_query = pyparsing.ZeroOrMore(
        pyparsing.Group(
            pyparsing.ZeroOrMore(
                papis_key_word + equal
            ) + papis_value
        )
    )
    parsed = papis_query.parseString(query_string)
    logger.debug("Parsed query: '%s'", parsed)

    # convert pyparsing results to our format
    results = []
    for result in parsed:
        n = len(result)
        if n == 1:
            search = result[0]
            doc_key = None
        elif n == 3:
            search = result[2]
            doc_key = result[0]
        else:
            continue

        results.append(ParseResult(search=search, doc_key=doc_key))

    return results
