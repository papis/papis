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

    #: A boolean indicating whether this is part of syntax or as search query
    syntax: bool
    #: A search string that was matched for this result.
    string: str
    #: A regex pattern constructed from the :attr:`search` using
    #: :func:`get_regex_from_search`.
    pattern: Pattern[str]
    #: A document key that was matched for this result, if any.
    doc_key: Optional[str] = None

    def __repr__(self) -> str:
        doc_key = "{!r}, ".format(self.doc_key) if self.doc_key is not None else ""
        return "[{}{!r}]".format(doc_key, self.string)

    def needsboolafter(self) -> bool:
        if self.syntax and self.string in ["and", "or", "not", "("]:
            return False
        else:
            return True

    def needsboolbefore(self) -> bool:
        if self.syntax and self.string in ["and", "or", ")"]:
            return False
        else:
            return True


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
    #: A format string (defaulting to :ref:`config-settings-match-format`) used
    #: to match the parsed search results if no document key is present.
    match_format: ClassVar[str] = papis.config.getstring("match-format")

    @classmethod
    def return_if_match(
        cls, doc: papis.document.Document
    ) -> Optional[papis.document.Document]:
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

        tokens = []
        for p in cls.parsed_search:
            if not p.syntax:
                tokens.append(
                    "True"
                    if cls.matcher(doc, p.pattern, cls.match_format, p.doc_key)
                    else "False"
                )
            else:
                tokens.append(p.string)

        result = eval(" ".join(tokens))
        match = doc if result else None

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
        """Parse the main query text and check its syntax.

        This method will also set :attr:`DocMatcher.parsed_search` to the
        resulting parsed query and it will return it too. If there is a syntax
        error it will log an error message and return None.

            >>> print(DocMatcher.parse('hello author : einstein'))
            [['hello'], ['and'], ['author', 'einstein']]
            >>> print(DocMatcher.parse(''))
            []
            >>> print(\
                DocMatcher.parse(\
                    '"hello world whatever :" tags : \\\'hello ::::\\\''))
            [['hello world whatever :'], ['and'], ['tags', 'hello ::::']]
            >>> print(DocMatcher.parse('hello'))
            [['hello']]

        :param search: a custom search text string that overwrite :attr:`search`.
        :returns: a parsed query.
        """
        if search is None:
            search = cls.search
        parsed_search = parse_query(search)

        if check_syntax(parsed_search):
            cls.parsed_search = parsed_search
        else:
            cls.parsed_search = []

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
        ".*{}.*".format(".*".join(map(re.escape, search.split()))), re.IGNORECASE
    )


def check_syntax(parsed: List[ParseResult]) -> bool:
    """Tests the syntax by replacing all search terms with True,
    then trying to evaluate the resulting string.
    """

    test = []
    for p in parsed:
        if not p.syntax:
            test.append("True")
        else:
            test.append(p.string)

    try:
        eval(" ".join(test))
        return True
    except SyntaxError:
        logger.error("Malformed query.")
        return False


def proofread(parsed: List[ParseResult]) -> List[ParseResult]:
    """Fixes a parsed query by inserting missing *and* operators.
    For instance:
    ' ein 192     photon' -> 'ein and 192 and photon'


    :param a parsed a search string.
    :returns: a fixed list of ParseResults or operators.
    """
    result = []
    last = len(parsed) - 1
    fixes = 0
    for idx, token in enumerate(parsed):
        result.append(token)
        if idx != last and token.needsboolafter() and parsed[idx + 1].needsboolbefore():
            # add 'and' when queries or syntax have have no operator in between
            result.append(
                ParseResult(
                    syntax=True, string="and", pattern=get_regex_from_search("")
                )
            )
            fixes += 1

    logger.debug("Fixed query by adding %s missing 'and' operator(s).", fixes)

    return result


def parse_query(query_string: str) -> List[ParseResult]:
    """Parse a query string using :mod:`pyparsing`.

    The query language implemented by this function for papis supports strings
    of the form::

        'hello author : Einstein or not (title: "Fancy Title: Part 1" tags)'

    which will result in

    .. code:: python

        results = [
            ParseResult(search="hello", pattern=<...>, doc_key=None),
            "and",
            ParseResult(search="Einstein", pattern=<...>, doc_key="author"),
            "or",
            "not",
            "(",
            ParseResult(search="Fancy Title: Part 1", pattern=<...>, doc_key="title"),
            "and",
            ParseResult(search="tags", pattern=<...>, doc_key=None),
            ")"
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

    papis_value_word = pyparsing.Word(
        pyparsing.alphanums + pyparsing.alphas8bit + "-._/"
    )

    papis_value = (
        pyparsing.QuotedString(quoteChar='"', escChar="\\", escQuote="\\")
        ^ pyparsing.QuotedString(quoteChar="'", escChar="\\", escQuote="\\")
        ^ papis_value_word
    )

    equal = pyparsing.Literal(":")

    key_phrase = pyparsing.Group(papis_key_word + equal + papis_value)

    operators = "and or not ( )"
    operator = pyparsing.oneOf(operators)

    papis_query = pyparsing.ZeroOrMore(key_phrase | papis_value | operator)

    parsed = papis_query.parseString(query_string).as_list()
    logger.debug("Parsed query: '%s'.", parsed)

    # convert pyparsing results to our format
    results = []
    for token in parsed:
        if token in operators.split():
            syntax = True
            string = token
        else:
            if type(token) is not list:
                syntax = False
                string = token
                doc_key = None
            elif len(token) == 3:
                syntax = False
                string = token[2]
                doc_key = token[0]
            else:
                continue

        pattern = get_regex_from_search(string)
        results.append(
            ParseResult(syntax=syntax, string=string, pattern=pattern, doc_key=doc_key)
        )

    return proofread(results)
