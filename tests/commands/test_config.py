import papis.config
import papis.logging

papis.logging.setup("DEBUG")


def with_default_config(fn):
    import os
    import tempfile
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as config:
            pass

        papis.config.set_config_file(config.name)
        papis.config.reset_configuration()

        result = fn(*args, **kwargs)

        papis.config.set_config_file(None)
        papis.config.reset_configuration()

        os.unlink(config.name)

        return result

    return wrapper


@with_default_config
def test_config_single_option() -> None:
    from papis.commands.config import run

    assert run(["editor"]) == {"editor": papis.config.get("editor")}
    assert run(["settings.editor"]) == {"editor": papis.config.get("editor")}
    assert run(["papers.dir"]) == {"dir": papis.config.get("dir", section="papers")}


@with_default_config
def test_config_section() -> None:
    # NOTE: imported to register the `bibtex` default settings
    import papis.commands.bibtex

    from papis.commands.config import run
    section = papis.config.get_general_settings_name()
    config = papis.config.get_configuration()
    defaults = papis.config.get_default_settings()

    # checks:
    # * non-existent key in non-existent section: `editor`
    # * non-overwritten keys in non-existent section: `auto-read`
    # * overwriting the section: `.notes-name`
    result = run(["editor", "auto-read", ".notes-name"], section="bibtex")
    assert "editor" not in result
    assert result == {
        "auto-read": papis.config.get("auto-read", section="bibtex"),
        "notes-name": papis.config.get("notes-name"),
        }

    # checks:
    # * existing key in given section: `dir`
    # * overwriting section: `.default-library`
    result = run(["dir", ".default-library"], section="papers")
    assert result == {
        "dir": config.default_info["papers"]["dir"],
        "default-library": config.default_info[section]["default-library"],
        }

    # checks:
    # * reading all the sections
    result = run([])
    assert result == defaults


@with_default_config
def test_config_section_defaults() -> None:
    from papis.commands.config import run
    defaults = papis.config.get_default_settings()

    # checks:
    # * non-existent key in given section: `editor`
    # * existing key in given section: `editmode`
    # * overwriting the section: `.notes-name`
    result = run(["editor", "editmode", ".notes-name"], section="tui", default=True)
    assert "editor" not in result
    assert result == {
        "editmode": papis.config.get("editmode", section="tui"),
        "notes-name": papis.config.get("notes-name"),
        }

    # checks:
    # * reading all the sections
    result = run([], default=True)
    assert result == defaults
