from typing import Any, Optional, NamedTuple, Tuple, Union


class FormattedString(NamedTuple):
    """A tuple that defines a ``(formatter, string)`` pair.

    In a configuration file, a formatted string can be defined as:

    .. code:: ini

        key = formatted_value
        other_key.formatter = other_formatted_value

    ... where the first key will use the default :confval:`formatter` and the second
    key will use the specified formatter. These keys can be read using
    :func:`papis.config.getformattedstring`.

    .. autoattribute:: formatter
    .. autoattribute:: value
    """

    #: The formatter that should be used on the string :attr:`value`. If none
    #: is provided, the default formatter is used, as defined by
    #: :confval:`formatter`.
    formatter: Optional[str]
    #: Value of the
    value: str

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return repr(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    # NOTE: __eq__ and __hash__ are implemented to ensure that formatted
    # strings can be used in 'click.option' with 'click.Choice'. This is not
    # very intuitive, as strings with the same text, but different formatters
    # will be equal. However, this is only an issue if the formatters use the
    # same templating language.

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.value == other
        elif isinstance(other, FormattedString):
            return self.value == other.value
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.value)


AnyString = Union[str, FormattedString]


def process_formatted_string_pair(
    key: str,
    value: AnyString
) -> Tuple[str, FormattedString]:
    """
    :param key: a document key in the format ``key[.formatter]``.
    :param value: an unformatted value.

    :returns: a ``(key, value)`` pair, where the formatter was removed from the
        *key* and the *value* is guaranteed to be a :class:`FormattedString`. If the
        *value* already defines a formatter, it is overwritten by the one defined
        by the *key*.
    """
    if "." in key:
        key, formatter = key.rsplit(".", maxsplit=1)
    else:
        formatter = None

    if isinstance(value, FormattedString):
        if formatter is not None:
            value = FormattedString(formatter, value.value)
    else:
        value = FormattedString(formatter, value)

    return key, value


no_documents_retrieved_message = "No documents retrieved"
no_folder_attached_to_document = (
    "Document has no folder attached (call 'Document.set_folder' first)")
time_format = "%Y-%m-%d-%H:%M:%S"
