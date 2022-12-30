"""
Logging
-------

Helper functions to set up logging used by ``papis``.

.. autofunction:: setup
.. autofunction:: get_logger
"""

import os
import sys
import logging
from typing import Optional, Union

import colorama


LEVEL_TO_COLOR = {
    "CRITICAL": colorama.Style.BRIGHT + colorama.Fore.RED,
    "ERROR": colorama.Style.BRIGHT + colorama.Fore.RED,
    "WARNING": colorama.Style.BRIGHT + colorama.Fore.YELLOW,
    "INFO": colorama.Fore.CYAN,
    "DEBUG": colorama.Fore.WHITE,
}


class ColoramaFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, str):
            record.msg = record.msg.format(c=colorama)

        if record.levelname in LEVEL_TO_COLOR:
            record.levelname = "{}{}{}".format(
                LEVEL_TO_COLOR[record.levelname],
                record.levelname,
                colorama.Style.RESET_ALL)

        if record.name.startswith("papis."):
            record.name = record.name[6:]

        return super().format(record)


def _disable_color(color: str = "auto") -> bool:
    return (
        color == "no"
        or (color == "auto" and not sys.stdout.isatty())
        # NOTE: https://no-color.org/
        or (color == "auto" and "NO_COLOR" in os.environ)
        )


def setup(level: Union[int, str],
          color: str = "auto",
          logfile: Optional[str] = None,
          verbose: bool = False) -> None:
    """
    :param level: default logging level (see
        :ref:`Logging Levels <logging:logging-levels>`).
    :param color: flag to control logging colors. It should be one of
        ``("always", "auto", "no")``.
    :param logfile: a path for a file in which to write log messages.
    :param verbose: make logger verbose (including debug information)
        regardless of the *level*.
    """

    if color not in ("always", "auto", "no"):
        raise ValueError("Unknown 'color' value: '{}'".format(color))

    if _disable_color(color):
        # Turn off colorama (strip escape sequences from the output)
        colorama.init(strip=True)
    else:
        colorama.init()

    if isinstance(level, str):
        try:
            level = getattr(logging, level)
        except AttributeError:
            raise ValueError("Unknown logger level: '{}'.".format(level))
    else:
        if logging.getLevelName(level).startswith("Level"):
            raise ValueError("Unknown logger level: '{}'.".format(level))

    log_format = (
        "{c.Fore.GREEN}%(name)s{c.Style.RESET_ALL}: %(message)s"
        .format(c=colorama))

    if verbose:
        level = logging.DEBUG
        log_format = "[%(relativeCreated)d %(levelname)s] {}".format(log_format)
    else:
        log_format = "[%(levelname)s] {}".format(log_format)

    if logfile is None:
        handler = logging.StreamHandler()       # type: logging.Handler
        handler.setFormatter(ColoramaFormatter(log_format))
    else:
        handler = logging.FileHandler(logfile, mode="a")

    # NOTE: only set the properties on the root 'papis' logger and have
    # sub-loggers inherit them, so that we don't override other packages
    logger = logging.getLogger("papis")
    logger.setLevel(level)
    logger.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name)
