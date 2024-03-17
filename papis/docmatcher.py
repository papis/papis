import re
from typing import Any, ClassVar, List, NamedTuple, Optional, Pattern, Protocol

import papis.config
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)


class ParseResult(NamedTuple):
    """Result from parsing a search string.

    For example, a search string such as ``"author:einstein"`` will result in

    .. code:: python

        r = ParseResult(search="einstein", pattern=<...>, doc_key="author")
    """

    #: A search string that was matched for this result.
    search: str
    #: A regex pattern constructed from the :attr:`search` using
    #: :func:`get_regex_from_search`.
    pattern: Pattern[str]
    #: A document key that was matched for this result, if any.
    doc_key: Optional[str]

    def __repr__(self) -> str:
        doc_key = f"{self.doc_key!r}, " if self.doc_key is not None else ""
        return f"[{doc_key}{self.search!r}]"


class MatcherCallable(Protocol):
    """A callable :class:`typing.Protocol` used to match a document for a given search.

    .. automethod:: __call__
    """

    def __call__(self,
                 document: papis.document.Document,
                 search: Pattern[str],
                 match_format: Optional[str] = None,
                 doc_key: Optional[str] = None,
                 ) -> Any:
        """Match a document's keys to a given search pattern.

        The matcher can decide whether the *match_format* or the *doc_key* take
        priority when matching against the given pattern in *search*. If
        possible, *doc_key* should be given priority as the more specific
        choice.

        :param search: a regex pattern to match the query against
            (see :attr:`ParseResult.pattern`).
        :param match_format: a format string (see :func:`papis.format.format`)
            to match against.
        :param doc_key: a specific key in the document to match against.
        :returns: *None* if the match fails and anything else otherwise.
        """


class DocMatcher:
    """This class implements the mini query language for papis.

    The (static) methods should be used as follows:

    * First, the search string has to be set::

        DocMatcher.set_search(search_string)

    * Then, the parse method should be called in order to decipher the
      *search_string*::

        DocMatcher.parse()

    * Finally, the :class:`DocMatcher` is ready to match documents with the input
      query via::

        DocMatcher.return_if_match(doc)
    """

    #: Search string from which the matcher is constructed.
    search: ClassVar[str] = ""
    #: A parsed version of the :attr:`search` string using :func:`parse_query`.
    parsed_search: ClassVar[Optional[List[ParseResult]]] = None
    #: A :class:`MatcherCallable` used to match the document to the
    #: :attr:`parsed_search`.
    matcher: ClassVar[Optional[MatcherCallable]] = None
    #: A format string (defaulting to :confval:`match-format`) used
    #: to match the parsed search results if no document key is present.
    match_format: ClassVar[str] = ""

    @classmethod
    def return_if_match(
            cls,
            doc: papis.document.Document) -> Optional[papis.document.Document]:
        """Use :attr:`DocMatcher.parsed_search` to match the *doc* against the query.

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

        :param doc: a papis document to match against.
        """

        match = None
        if cls.parsed_search is None or cls.matcher is None:
            return match

        for p in cls.parsed_search:
            match = (
                doc if cls.matcher(doc, p.pattern, cls.match_format, p.doc_key)
                else None)

            if not match:
                break

        return match

    @classmethod
    def set_search(cls, search: str) -> None:
        """Set the search for this instance of the matcher.

            >>> DocMatcher.set_search('author:Hummel')
            >>> DocMatcher.search
            'author:Hummel'
        """

        cls.search = search

    @classmethod
    def set_matcher(cls, matcher: MatcherCallable) -> None:
        """Set the matcher callable for the search.

            >>> from papis.database.cache import match_document
            >>> DocMatcher.set_matcher(match_document)
        """
        cls.matcher = matcher

    @classmethod
    def parse(cls, search: Optional[str] = None) -> List[ParseResult]:
        """Parse the main query text.

        This method will also set :attr:`DocMatcher.parsed_search` to the
        resulting parsed query and it will return it too.

            >>> print(DocMatcher.parse('hello author : einstein'))
            [['hello'], ['author', 'einstein']]
            >>> print(DocMatcher.parse(''))
            []
            >>> print(\
                DocMatcher.parse(\
                    '"hello world whatever :" tags : \\\'hello ::::\\\''))
            [['hello world whatever :'], ['tags', 'hello ::::']]
            >>> print(DocMatcher.parse('hello'))
            [['hello']]

        :param search: a custom search text string that overwrite :attr:`search`.
        :returns: a parsed query.
        """
        if search is None:
            search = cls.search

        cls.match_format = papis.config.getstring("match-format")
        cls.parsed_search = parse_query(search)

        return cls.parsed_search


def get_regex_from_search(search: str) -> Pattern[str]:
    r"""Creates a default regex from a search string.

        >>> get_regex_from_search(' ein 192     photon').pattern
        '.*ein.*192.*photon.*'
        >>> get_regex_from_search('{1234}').pattern
        '.*\\{1234\\}.*'

    :param search: a valid search string.
    :returns: a regular expression representing the search string, which is
        properly escaped and allows for multiple spaces.
    """
    return re.compile(
        ".*{}.*".format(".*".join(map(re.escape, search.split()))),
        re.IGNORECASE)


def parse_query(query_string: str) -> List[ParseResult]:
    """Parse a query string using :mod:`pyparsing`.

    The query language implemented by this function for papis supports strings
    of the form::

        'hello author : Einstein    title: "Fancy Title: Part 1" tags'

    which will result in

    .. code:: python

        results = [
            ParseResult(search="hello", pattern=<...>, doc_key=None),
            ParseResult(search="Einstein", pattern=<...>, doc_key="author"),
            ParseResult(search="Fancy Title: Part 1", pattern=<...>, doc_key="title"),
            ParseResult(search="tags", pattern=<...>, doc_key=None),
        ]

    We can see there that constructs of the form ``"key:value"`` with the colon
    as a separator are recognized and parsed to document keys with the color.
    They can be escaped by enclosing them in quotes. Otherwise, each individual
    word in the search query will give another :class:`ParseResult`. Each
    search term can contain additional regex characters.

    :param query_string: a search string to parse into a structured format.
    :returns: a list of parsing results for each token in the query string.
    """

    import pyparsing
    logger.debug("Parsing query: '%s'.", query_string)

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
    logger.debug("Parsed query: '%s'.", parsed)

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

        pattern = get_regex_from_search(search)
        results.append(ParseResult(search=search, pattern=pattern, doc_key=doc_key))

    return results
