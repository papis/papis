from typing import Any, ClassVar

import papis.logging
from papis.document import Document, DocumentLike, describe, from_data
from papis.format import FormatFailedError, Formatter, unescape

logger = papis.logging.get_logger(__name__)


class Jinja2Formatter(Formatter):
    """Construct a string using `Jinja2 <https://palletsprojects.com/p/jinja/>`__
    templates.

    This formatter is named ``"jinja2"`` and can be set using the
    :confval:`formatter` setting in the configuration file. The
    format pattern has access to the ``doc`` variable, that is always a
    :class:`papis.document.Document`. A pattern using this formatter can look
    like:

    .. code:: python

        "{{ doc.year }} - {{ doc.author_list[0].family }} - {{ doc.title }}"

    This formatter supports the whole range of Jinja2 control structures and
    `filters <https://jinja.palletsprojects.com/en/3.1.x/templates/#filters>`__
    so more advanced string processing is possible. For example, we can titlecase
    the title using:

    .. code:: python

        "{{ doc.title | title }}"

    or give a default value if a key is missing in the document using:

    .. code:: python

        "{{ doc.isbn | default('ISBN-NONE', true) }}"
    """

    name: ClassVar[str] = "jinja2"

    env: ClassVar[Any] = None
    """The ``jinja2`` Environment used by the formatter. This should be obtained
    with :meth:`~Jinja2Formatter.get_environment()` (cached) and modified as
    required (e.g. by adding filters).
    """

    def __init__(self) -> None:
        super().__init__()

        try:
            import jinja2  # noqa: F401
        except ImportError as exc:
            logger.error(
                "The 'jinja2' formatter requires the 'jinja2' library. "
                "To use this functionality install it using e.g. "
                "'pip install jinja2'.", exc_info=exc)
            raise exc

    @classmethod
    def get_environment(cls, *, force: bool = False) -> Any:
        """Construct and cache the ``jinja2`` environment used by the formatter.

        The environment is created on the first call to :meth:`format` and cached
        for future use. If it should be recreated after that, this function can
        be called with *force* set to *True*.

        :arg force: if *True*, the environment will be recreated.
        """

        if cls.env is None or force:
            from jinja2 import Environment

            # NOTE: this will kindly autoescape apostrophes otherwise
            env = Environment(autoescape=False)
            env.shared = True
            cls.env = env

        return cls.env

    def format(self,
               fmt: str,
               doc: DocumentLike,
               doc_key: str = "",
               additional: dict[str, Any] | None = None,
               default: str | None = None) -> str:
        if additional is None:
            additional = {}

        fmt = unescape(fmt)
        if not isinstance(doc, Document):
            doc = from_data(doc)

        doc_name = doc_key or self.default_doc_name
        env = self.get_environment()

        try:
            return str(env.from_string(fmt).render(**{doc_name: doc}, **additional))
        except Exception as exc:
            if default is not None:
                logger.warning("Could not format pattern '%s' for document '%s'",
                               fmt, describe(doc), exc_info=exc)
                return default
            else:
                raise FormatFailedError(fmt) from exc
