import logging
from typing import Optional, Any, Callable, TYPE_CHECKING

import papis.config
import papis.document

if TYPE_CHECKING:
    import pyparsing

logger = logging.getLogger(__name__)

MATCHER_TYPE = Callable[[papis.document.Document, str, Optional[str]], Any]


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
    parsed_search = None  # type: pyparsing.ParseResults
    doc_format = "{%s[DOC_KEY]}" % (papis.config.getstring("format-doc-name"))
    matcher = None  # type: Optional[MATCHER_TYPE]

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
        if cls.parsed_search is None:
            return match

        for parsed in cls.parsed_search:
            if len(parsed) == 1:
                search = parsed[0]
                sformat = None
            elif len(parsed) == 3:
                search = parsed[2]
                sformat = cls.doc_format.replace("DOC_KEY", parsed[0])

            if cls.matcher is not None:
                match = doc if cls.matcher(doc, search, sformat) else None
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
    def parse(cls, search: Optional[str] = None) -> "pyparsing.ParseResults":
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


def parse_query(query_string: str) -> "pyparsing.ParseResults":
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

    return parsed
