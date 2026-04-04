from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, NamedTuple, Protocol
from warnings import warn

import papis.config
import papis.logging
from papis.strings import AnyString, FormatPattern

if TYPE_CHECKING:
    from collections.abc import Callable

    from papis.document import Document

logger = papis.logging.get_logger(__name__)


class ParseResult(NamedTuple):
    """Result from parsing a search string using :func:`parse_query`.

    For example, a search string such as ``"author:einstein"`` will result in:

    .. code:: python

        r = ParseResult(search="einstein", pattern=<...>, doc_key="author")
    """

    #: A search string that was matched for this result.
    search: str
    #: A regex pattern constructed from the :attr:`search` using
    #: :func:`get_regex_from_search`.
    pattern: re.Pattern[str]
    #: A document key that was matched for this result, if any.
    doc_key: str | None

    def __repr__(self) -> str:
        doc_key = f"{self.doc_key!r}, " if self.doc_key is not None else ""
        return f"[{doc_key}{self.search!r}]"


class MatcherCallable(Protocol):
    """A callable :class:`typing.Protocol` used to match a document for a given search.

    .. automethod:: __call__
    """

    def __call__(self,
                 document: Document,
                 search: re.Pattern[str],
                 match_format: AnyString | None = None,
                 doc_key: str | None = None,
                 ) -> Any:
        """Match a document's keys to a given search pattern.

        The matcher can decide whether the *match_format* or the *doc_key* take
        priority when matching against the given pattern in *search*. If
        possible, *doc_key* should be given priority as the more specific
        choice.

        :param search: a regex pattern to match the query against
            (see :attr:`ParseResult.pattern`).
        :param match_format: a format pattern (see :func:`papis.format.format`)
            to match against.
        :param doc_key: a specific key in the document to match against.
        :returns: *None* if the match fails and anything else otherwise.
        """


# NOTE: this is deprecated because it doesn't work well with multiprocessing in
# Python 3.14. In particular, it does not pickle properly when used with the
# 'forkserver' backend on Linux and friends.
class DocMatcher:
    search: ClassVar[str] = ""
    parsed_search: ClassVar[list[ParseResult] | None] = None
    matcher: ClassVar[MatcherCallable | None] = None
    match_format: ClassVar[FormatPattern] = FormatPattern(None, "")

    @classmethod
    def return_if_match(
            cls,
            doc: Document) -> Document | None:
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
        cls.search = search

    @classmethod
    def set_matcher(cls, matcher: MatcherCallable) -> None:
        cls.matcher = matcher

    @classmethod
    def parse(cls, search: str | None = None) -> list[ParseResult]:
        warn("'DocMatcher' is deprecated and will be removed in Papis v0.16. Use "
             "'make_document_matcher' instead.",
             DeprecationWarning, stacklevel=2)

        if search is None:
            search = cls.search

        cls.match_format = papis.config.getformatpattern("match-format")
        cls.parsed_search = parse_query(search)

        return cls.parsed_search


@dataclass(frozen=True)
class DocumentMatcher:
    """A class that can be used to match documents to a query.

    .. automethod:: __call__
    """

    #: Initial search string used for the matcher.
    search: str
    #: The query resulting from :func:`parse_query`.
    query: list[ParseResult]
    #: A format that is used to match a document against.
    match_format: FormatPattern
    #: A callable used to match a document to the :attr:`query` using the
    #: :attr:`match_format`.
    matcher: MatcherCallable

    def __call__(self, doc: Document) -> Document | None:
        """Use the stored :attr:`query` to match the document.

        """
        match = None
        for p in self.query:
            match = (
                doc
                if self.matcher(doc, p.pattern, self.match_format, p.doc_key)
                else None)

            # NOTE: exit if a pattern did not match the document => means the
            # document does not fully match the search query
            if not match:
                break

        return match


def make_document_matcher(
        search: str, *,
        matcher: MatcherCallable | None = None,
        match_format: AnyString | None = None,
    ) -> Callable[[Document], Document | None]:
    """Create a callable that can be used to match documents against the given
    *search* query.

        >>> from papis.document import from_data
        >>> doc = from_data({'title': 'einstein'})
        >>> matcher = make_document_matcher('einste')
        >>> matcher(doc) is not None
        True
        >>> matcher = make_document_matcher('heisenberg')
        >>> matcher(doc) is not None
        False
        >>> matcher = make_document_matcher('title : ein')
        >>> matcher(doc) is not None
        True

    :param matcher: a callable used to match the documents. This defaults to
        :func:`~papis.database.cache.match_document`.
    :param match_format: a format used to match against the query. This defaults
        to :confval:`match-format`.
    """
    if matcher is None:
        from papis.database.cache import match_document
        matcher = match_document

    if match_format is None:
        match_format = papis.config.getformatpattern("match-format")

    if isinstance(match_format, str):
        match_format = FormatPattern(None, match_format)

    query = parse_query(search)
    return DocumentMatcher(
        search=search, query=query, match_format=match_format, matcher=matcher
    )


def get_regex_from_search(search: str) -> re.Pattern[str]:
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


def parse_query(query_string: str) -> list[ParseResult]:
    """Parse a query string using :mod:`pyparsing`.

    The query language implemented by this function for Papis supports strings
    of the form::

        'hello author : Einstein    title: "Fancy Title: Part 1" tags'

    which will result in:

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

        >>> print(parse_query('hello author : einstein'))
        [['hello'], ['author', 'einstein']]
        >>> print(parse_query(''))
        []
        >>> print(\
            parse_query(\
                '"hello world whatever :" tags : \\\'hello ::::\\\''))
        [['hello world whatever :'], ['tags', 'hello ::::']]
        >>> print(parse_query('hello'))
        [['hello']]

    :param query_string: a search string to parse into a structured format.
    :returns: a list of parsing results for each token in the query string.
    """

    import pyparsing
    logger.debug("Parsing query: '%s'.", query_string)

    papis_key_word = pyparsing.Word(pyparsing.alphanums + "-._/")
    papis_value_word = pyparsing.Word(pyparsing.alphanums + "-._/()")

    papis_value = pyparsing.QuotedString(
        quote_char='"', esc_char="\\", esc_quote="\\"
    ) ^ pyparsing.QuotedString(
        quote_char="'", esc_char="\\", esc_quote="\\"
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
    parsed = papis_query.parse_string(query_string)
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
