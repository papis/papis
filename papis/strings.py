from typing import Any, NamedTuple, Optional, Tuple, Union


class FormatPattern(NamedTuple):
    """A tuple that defines a ``(formatter, string)`` pair.

    In a configuration file, a format pattern can be defined as:

    .. code:: ini

        key = pattern
        other_key.formatter = other_pattern

    where the first key will use the default :confval:`formatter` and the second
    key will use the specified formatter. These keys can be read using
    :func:`papis.config.getformatpattern`.

    .. autoattribute:: formatter
    .. autoattribute:: pattern
    """

    #: The formatter that should be used on the string :attr:`pattern`. If none
    #: is provided, the default formatter is used, as defined by
    #: :confval:`formatter`.
    formatter: Optional[str]
    #: Pattern that should be evaluated by the *formatter*.
    pattern: str

    def __str__(self) -> str:
        return self.pattern

    def __repr__(self) -> str:
        return repr(self.pattern)

    def __bool__(self) -> bool:
        return bool(self.pattern)

    # NOTE: __eq__ and __hash__ are implemented to ensure that format
    # pattern can be used in 'click.option' with 'click.Choice'. This is not
    # very intuitive, as strings with the same text, but different formatters
    # will be equal. However, this is only an issue if the formatters use the
    # same templating language.

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.pattern == other
        elif isinstance(other, FormatPattern):
            return self.pattern == other.pattern
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.pattern)


AnyString = Union[str, FormatPattern]


def process_format_pattern_pair(
    key: str,
    pattern: AnyString
) -> Tuple[str, FormatPattern]:
    """
    :param key: a document key in the format ``key[.formatter]``.
    :param pattern: an unformatted pattern.

    :returns: a ``(key, pattern)`` pair, where the formatter was removed from the
        *key* and the *pattern* is guaranteed to be a :class:`FormatPattern`. If the
        *pattern* already defines a formatter, it is overwritten by the one defined
        by the *key*.
    """
    if "." in key:
        key, formatter = key.rsplit(".", maxsplit=1)
    else:
        formatter = None

    if isinstance(pattern, FormatPattern):
        if formatter is not None:
            pattern = FormatPattern(formatter, pattern.pattern)
    else:
        pattern = FormatPattern(formatter, pattern)

    return key, pattern


no_documents_retrieved_message = "No documents retrieved"
no_folder_attached_to_document = (
    "Document has no folder attached (call 'Document.set_folder' first)")
time_format = "%Y-%m-%d-%H:%M:%S"
