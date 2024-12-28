"""
The ``config`` command allows you to query the settings used by Papis on your
system.

Examples
^^^^^^^^

The ``config`` command returns the value used by Papis. Therefore, if you
have not customized some setting, it will return the default value. In contrast,
if you have customized it, it will return the value set in the configuration
file. For example, to find out to what your "default-library" is set to, call:

.. code::

    papis config default-library

The ``config`` command can also be used to query a settings' default
value. This is done by adding the ``--default`` flag. This ignores all
settings set in your Papis configuration file (note, however, that
settings set in a ``config.py`` script can count as default values). Check the
default "default-library" with:

.. code::

    papis config --default default-library

Settings from a specific section in the configuration file can also be
accessed. To take an example, the :ref:`papis bibtex <command-bibtex>` command's
settings can be accessed with:

.. code::

    papis config --section bibtex
    papis config --default --section bibtex

or with ``papis config`` (without the section argument) to show the settings
available for all the known sections.

You can also query a specific setting within a section. For example like this:

.. code::

    papis config --section bibtex default-read-bibfile
    papis config --default --section bibtex default-read-bibfile

Alternatively, you can also use the ``<section.setting>`` format to query the
value of a setting in a specific `section`:

.. code::

    papis config bibtex.default-read-bibfile
    papis config --default bibtex.default-read-bibfile

For some more advanced usage, we can also query multiple settings at once. Here,
sections specified with ``<section>.<setting>`` override the section specified by
``--setting <section>``. This can be achieved by:

.. code::

    papis config --section sec1 key1 key2 key3 sec2.key4 sec3.key5

You can find a list of all available settings in the configuration section
at :ref:`general-settings`. Commands and other plugins can define their own
settings, which are documented separately.

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.config:cli
    :prog: papis config
"""

from typing import Any, Dict, List, Optional, Tuple

import click
import colorama

import papis.cli
import papis.config
import papis.commands
import papis.logging

logger = papis.logging.get_logger(__name__)


def format_option(key: str, value: Any) -> str:
    c = colorama
    return (
        f"{c.Style.BRIGHT}{key}{c.Style.NORMAL} "
        f"= {c.Fore.GREEN}{value!r}{c.Style.RESET_ALL}")


def parse_option(
        option: str, default_section: Optional[str]
        ) -> Tuple[Optional[str], str]:
    """
    :returns: a ``(section, key)`` tuple parsed from *option*.
    """
    from papis.format import get_available_formatters
    formatters = set(get_available_formatters())

    parts = option.split(".")
    key = section = None
    if len(parts) == 1:
        key = parts[0]
        section = default_section
    elif len(parts) == 2:
        if parts[1] in formatters:
            section = default_section
            key = option
        else:
            section = parts[0] if parts[0] else None
            key = parts[1]
    else:
        raise ValueError(f"Unsupported option format: '{option}'")

    return section, key


def _get_option_safe(
        option: str, default_section: Optional[str], default: bool = False,
        ) -> Tuple[Optional[str], Optional[str]]:
    key = option
    value = None

    try:
        section, key = parse_option(option, default_section)
    except ValueError:
        logger.error(
            "Options should be in a <section>.<key> or <key> format: got '%s'.",
            option)
        return key, value

    if default:
        if section is None:
            section = papis.config.get_general_settings_name()

        defaults = papis.config.get_default_settings()
        try:
            value = defaults[section][key]
        except KeyError:
            logger.error(
                "No default value for setting '%s' found in section '%s'.",
                key, section)
    else:
        try:
            value = papis.config.get(key, section=section)
        except papis.exceptions.DefaultSettingValueMissing as exc:
            logger.error("No value for setting '%s' found in section '%s'.",
                         key, section, exc_info=exc)

    return key, value


def run(
        options: List[str],
        section: Optional[str] = None,
        default: bool = False,
        ) -> Dict[str, Any]:
    """
    :param options: a list of strings, each in a format ``[<section>].<key>``
        (i.e. where the section is optional).
    :param section: a default section to query for configuration settings.
    :param default: if *True*, return hardcoded default values, otherwise return
        the values from the configuration file.
    """
    config = papis.config.get_configuration()
    result: Dict[str, Any] = {}

    if len(options) == 0:
        # NOTE: no options given -> just get all the settings
        defaults = papis.config.get_default_settings()
        if default:
            if section is None:
                result = defaults
            elif section in defaults:
                result = defaults[section]
            else:
                logger.error("Section '%s' does not exist in defaults. "
                             "Known sections are '%s'.",
                             section, "', '".join(defaults))
        else:
            if section is None:
                for sec in defaults:
                    result[sec] = defaults[sec].copy()
                    if sec in config:
                        result.update({
                            key: papis.config.get(key, section=sec)
                            for key in config.options(sec) if key in result
                            })
            elif section in defaults:
                result = defaults[section].copy()
                if section in config:
                    result.update({
                        key: papis.config.get(key, section=section)
                        for key in config.options(section) if key in result
                        })
            elif section in config:
                # NOTE: libraries are in the config but not in the defaults,
                # so we just print whatever settings are in there.
                result = {key: config[section][key] for key in config.options(section)}
            else:
                logger.error("Section '%s' not found in configuration file. "
                             "Known sections are '%s'.",
                             section, "', '".join(config.sections()))
    else:
        # NOTE: options given -> print only chosen options
        for option in options:
            key, value = _get_option_safe(option, section, default=default)
            if value is not None:
                assert key is not None
                result[key] = value

    return result


@click.command("config")
@click.help_option("--help", "-h")
@click.argument("options", nargs=-1)
@click.option(
    "-s", "--section",
    help="select a default section for the options",
    default=None)
@papis.cli.bool_flag(
    "-d", "--default",
    help="List default configuration setting values, instead of those in the "
         "configuration file")
@papis.cli.bool_flag(
    "--json", "print_json",
    help="Print settings in a JSON format")
def cli(options: List[str],
        section: Optional[str],
        default: bool,
        print_json: bool) -> None:
    """Print configuration values"""
    if len(options) == 1:
        # NOTE: a single option is printed directly for a bit of backwards
        # compatibility and easier use in shell scripts, so remove with care!
        _, value = _get_option_safe(options[0], section, default=default)
        if value is not None:
            click.echo(value)
        return

    result = run(options, section=section, default=default)
    if not result:
        return

    if print_json:
        import json
        click.echo(json.dumps(result, indent=2))
        return

    lines = []
    if len(options) == 0 and section is None:
        # NOTE: no inputs prints all of the sections
        is_first = True
        for section, settings in result.items():
            if not is_first:
                lines.append("")

            is_first = False
            lines.append(f"[{section}]")

            for key, value in settings.items():
                lines.append(format_option(key, value))
    else:
        if section is not None and all("." not in o for o in options):
            lines.append(f"[{section}]")

        for key, value in result.items():
            lines.append(format_option(key, value))

    click.echo("\n".join(lines))
