import os
import sys
import logging
from typing import Any, Optional, Tuple, Union

import click
import colorama


PAPIS_DEBUG = "PAPIS_DEBUG" in os.environ
LEVEL_TO_COLOR = {
    "CRITICAL": colorama.Style.BRIGHT + colorama.Fore.RED,
    "ERROR": colorama.Style.BRIGHT + colorama.Fore.RED,
    "WARNING": colorama.Style.BRIGHT + colorama.Fore.YELLOW,
    "INFO": colorama.Fore.CYAN,
    "DEBUG": colorama.Fore.WHITE,
}


def debug(msg: str, *args: Any) -> None:
    if PAPIS_DEBUG:
        click.echo(msg % args)


class ColoramaFormatter(logging.Formatter):
    """A custom logging formatter that uses ``colorama``."""

    def __init__(self, log_format: str, full_tb: bool = False) -> None:
        super().__init__(log_format)

        #: A flag to denote whether a full traceback should be displayed when
        #: used with ``logger.info(..., exc_info=ext)``.
        self.full_tb: bool = full_tb

    def formatException(self, exc_info: Tuple[Any, ...]) -> str:    # noqa: N802
        """Format and return the specified exception information as a string.

        If :attr:`full_tb` is *True*, then the full traceback is shown. Otherwise,
        a short inline description is given.
        """
        import io
        import traceback

        if self.full_tb:
            buffer = io.StringIO()
            traceback.print_exception(exc_info[0], exc_info[1], exc_info[2],
                                      None, buffer)
            tb = buffer.getvalue().strip()
            buffer.close()

            return "\n".join(f"  ┆ {line}" for line in tb.split("\n"))
        else:
            msg = str(exc_info[1])
            if len(msg) > 48:
                msg = "{}...".format(msg[:48].rsplit(" ", 1)[0])

            return (
                "(Caught exception '{}: {}'. Use `--log DEBUG` to see traceback)"
                .format(exc_info[0].__name__, msg))

    def format(self, record: logging.LogRecord) -> str:
        """Format the specified record as text.

        This adds color coding to the logging levels, includes the exception
        into the message, removes the ``papis`` namespace from the name, etc. Any
        formatting of the logging output is made here.
        """

        if isinstance(record.msg, str):
            record.msg = record.msg.format(c=colorama)

        if record.levelname in LEVEL_TO_COLOR:
            record.levelname = "{}{}{}".format(
                LEVEL_TO_COLOR[record.levelname],
                record.levelname,
                colorama.Style.RESET_ALL)

        if record.name.startswith("papis."):
            record.name = record.name[6:]

        if record.exc_info and not self.full_tb:
            exc_text = self.formatException(record.exc_info)
            record.msg = f"{record.msg} {exc_text}"
            record.exc_text = None
            record.exc_info = None

        return super().format(record)


def _disable_color(color: str = "auto") -> bool:
    return (
        color == "no"
        or (color == "auto" and not sys.stdout.isatty())
        # NOTE: https://no-color.org/
        or (color == "auto" and "NO_COLOR" in os.environ)
        )


def setup(level: Optional[Union[int, str]] = None,
          color: Optional[str] = None,
          logfile: Optional[str] = None,
          verbose: Optional[bool] = None) -> None:
    """Set up formatting and handlers for the root level Papis logger.

    :param level: default logging level (see :mod:`logging`). By default, this
        takes values from the ``PAPIS_LOG_LEVEL`` environment variable and
        falls back to ``"INFO"``.
    :param color: flag to control logging colors. It should be one of
        ``("always", "auto", "no")``. By default, this takes values from the
        ``PAPIS_LOG_COLOR`` environment variable and falls back to ``"auto"``.
    :param logfile: a path for a file in which to write log messages. By default,
        this takes values from the ``PAPIS_LOG_FILE`` environment variable and
        falls back to *None*.
    :param verbose: make logger verbose (including debug information)
        regardless of the *level*. By default, this takes values from the
        ``PAPIS_DEBUG`` environment variable and falls back to *False*.
    """

    if level is None:
        level = os.environ.get("PAPIS_LOG_LEVEL", "INFO").upper()

    if color is None:
        color = os.environ.get("PAPIS_LOG_COLOR", "auto")

    if logfile is None:
        logfile = os.environ.get("PAPIS_LOG_FILE")

    if verbose is None:
        try:
            verbose = bool(int(os.environ.get("PAPIS_DEBUG", "0")))
        except ValueError:
            verbose = False

    if color not in ("always", "auto", "no"):
        raise ValueError(f"Unknown 'color' value: '{color}'")

    if _disable_color(color):
        # Turn off colorama (strip escape sequences from the output)
        colorama.init(strip=True)
    else:
        colorama.init()

    if isinstance(level, str):
        try:
            level = int(getattr(logging, level))
        except AttributeError:
            raise ValueError(f"Unknown logger level: '{level}'") from None
    else:
        if logging.getLevelName(level).startswith("Level"):
            raise ValueError(f"Unknown logger level: '{level}'")

    log_format = (
        "{c.Fore.GREEN}%(name)s{c.Style.RESET_ALL}: %(message)s"
        .format(c=colorama))

    if verbose:
        level = logging.DEBUG
        log_format = f"[%(relativeCreated)d %(levelname)s] {log_format}"
    else:
        log_format = f"[%(levelname)s] {log_format}"

    if logfile is None:
        full_tb = level == logging.DEBUG
        handler: logging.Handler = logging.StreamHandler()
        handler.setFormatter(ColoramaFormatter(log_format, full_tb=full_tb))
    else:
        handler = logging.FileHandler(logfile, mode="a")

    # NOTE: only set the properties on the root 'papis' logger and have
    # sub-loggers inherit them, so that we don't override other packages
    logger = logging.getLogger("papis")
    logger.setLevel(level)
    logger.addHandler(handler)


def reset(level: Optional[Union[int, str]] = None,
          color: Optional[str] = None,
          logfile: Optional[str] = None,
          verbose: Optional[bool] = None) -> None:
    """Reset the root level Papis logger.

    This function removes all the custom handlers and resets the logger
    before calling :func:`setup`.
    """
    logger = logging.getLogger("papis")
    for filter in logger.filters:
        logger.removeFilter(filter)

    for handler in logger.handlers:
        logger.removeHandler(handler)

    setup(level, color=color, logfile=logfile, verbose=verbose)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for the given name under the ``papis`` namespace.

    :arg name: the provisional name of the logger instance.
    :returns: a :class:`logging.Logger` under the ``papis`` namespace, i.e. with a
        name such as ``papis.<name>``.
    """
    if name is None or name.startswith("papis."):
        return logging.getLogger(name)
    else:
        return logging.getLogger("papis").getChild(name)
