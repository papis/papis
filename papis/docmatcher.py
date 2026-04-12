from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol
from warnings import warn

from lark import Token, Transformer

import papis.config
import papis.logging
from papis.format import format
from papis.strings import AnyString, FormatPattern

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from papis.document import Document

logger = papis.logging.get_logger(__name__)


class MatcherCallable(Protocol):
    def __call__(self,
                 document: Document,
                 search: re.Pattern[str],
                 match_format: AnyString | None = None,
                 doc_key: str | None = None,
                 ) -> Any:
        pass


@dataclass(frozen=True)
class DocumentMatcher:
    """A class that can be used to match documents to a query.

    .. automethod:: __call__
    """

    #: Initial search string used for the matcher.
    search: str
    #: The query resulting from :func:`parse_query`.
    query: QueryResult
    #: A format that is used to match a document against.
    match_format: FormatPattern

    # deprecated
    matcher: MatcherCallable | None

    def __call__(self, doc: Document) -> bool:
        """Use the stored :attr:`query` to match the document."""
        return self.query.match(doc, self.match_format)


def make_document_matcher(
        search: str, *,
        matcher: MatcherCallable | None = None,
        match_format: AnyString | None = None,
    ) -> Callable[[Document], bool]:
    """Create a callable that can be used to match documents against the given
    *search* query.

        >>> from papis.document import from_data
        >>> doc = from_data({'title': 'einstein'})
        >>> matcher = make_document_matcher('einste')
        >>> matcher(doc)
        True
        >>> matcher = make_document_matcher('heisenberg')
        >>> matcher(doc)
        False
        >>> matcher = make_document_matcher('title : ein')
        >>> matcher(doc)
        True

    :param matcher: a callable used to match the documents. This defaults to
        :func:`~papis.database.cache.match_document`.
    :param match_format: a format used to match against the query. This defaults
        to :confval:`match-format`.
    """
    if matcher is not None:
        warn("Passing 'matcher' to 'make_document_matcher' is deprecated and "
             "will be removed in Papis 0.17.", DeprecationWarning, stacklevel=2)

    if match_format is None:
        match_format = papis.config.getformatpattern("match-format")

    if isinstance(match_format, str):
        match_format = FormatPattern(None, match_format)

    query = parse_query(search)
    return DocumentMatcher(
        search=search, query=query, match_format=match_format, matcher=None
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
    search = search.strip("'").strip('"')
    return re.compile(
        ".*{}.*".format(".*".join(map(re.escape, search.split()))),
        re.IGNORECASE)


_QUERY_GRAMMAR = r"""\
start: item*

?item: pair | term

term: ESCAPED_STRING | WORD
pair: key ":" value

key: WORD
value: ESCAPED_STRING | WORD
WORD: /[\w\-._\/()\[\]{}*+?]+/u
ESCAPED_STRING: /"([^"\\]|\\.)*"|'([^'\\]|\\.)*'/

%import common.WS
%ignore WS
"""


class QueryItem(ABC):
    @abstractmethod
    def match(self, doc: Document, match_format: FormatPattern) -> bool:
        pass


@dataclass
class QueryResult(QueryItem):
    children: Sequence[QueryItem]

    def match(self, doc: Document, match_format: FormatPattern) -> bool:
        return all(child.match(doc, match_format) for child in self.children)


@dataclass
class Term(QueryItem):
    query: str
    pattern: re.Pattern[str]

    def match(self, doc: Document, match_format: FormatPattern) -> bool:
        return self.pattern.match(format(match_format, doc)) is not None


@dataclass
class Pair(QueryItem):
    key: str
    query: str
    pattern: re.Pattern[str]

    def match(self, doc: Document, match_format: FormatPattern) -> bool:
        value = doc.get(self.key)
        if value is None:
            return False

        return self.pattern.match(str(value)) is not None


class QueryTransformer(Transformer[Any, QueryResult]):
    def start(self, children: list[QueryItem]) -> QueryResult:  # noqa: PLR6301
        return QueryResult(children)

    def term(self, children: Sequence[Token]) -> Term:  # noqa: PLR6301
        term = str(children[0])
        return Term(term, get_regex_from_search(term))

    def pair(self, children: Sequence[str]) -> Pair:  # noqa: PLR6301
        key, value = children
        return Pair(key, value, get_regex_from_search(value))

    def key(self, children: Sequence[Token]) -> str:  # noqa: PLR6301
        return str(children[0])

    def value(self, children: Sequence[Token]) -> str:  # noqa: PLR6301
        return str(children[0])


def parse_query(query_string: str) -> QueryResult:
    """Parse a query string to a structured query language.

    The query language implemented by this function supports strings of the form::

        'hello author : Einstein    title: "Fancy Title: Part 1" tags'

    We can see there that constructs of the form ``"key:value"``, with the
    colon as a separator, are recognized and parsed to document keys with the
    value. They can be escaped by enclosing them in additional quotes.
    Otherwise, each individual word in the search query will give result in a
    separate item. Each search term can contain additional :mod:`re` regex
    characters.

        >>> parse_query('hello author : einstein')
        QueryResult(children=[Term(query='hello', ...), Pair(key='author', query='einstein', ...)])
        >>> parse_query('')
        QueryResult(children=[])
        >>> parse_query('"hello world" tags : \\\'hello :\\\'')
        QueryResult(children=[Term(query='"hello world"', ...), Pair(key='tags', query="'hello :'", ...)])
        >>> parse_query('hello')
        QueryResult(children=[Term(query='hello', ...)])

    :param query_string: a search string to parse into a structured format.
    :returns: a parsing result for the query string.
    """  # noqa: E501

    logger.debug("Parsing query: '%s'.", query_string)

    import lark

    parser = lark.Lark(_QUERY_GRAMMAR, parser="lalr")
    tree = parser.parse(query_string)
    query = QueryTransformer().transform(tree)

    logger.debug("Parsed query:\n%s", tree.pretty())

    return query
