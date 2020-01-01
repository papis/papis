import click
import papis.config
import difflib


class AliasedGroup(click.Group):
    """
    This group command is taken from
        http://click.palletsprojects.com/en/5.x/advanced/#command-aliases
    and is to be used for groups with aliases
    """

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = difflib.get_close_matches(
            cmd_name, self.list_commands(ctx), n=2)
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


def query_option(**attrs):
    """Adds a ``query`` argument as a decorator"""
    def decorator(f):
        attrs.setdefault(
            'default',
            lambda: papis.config.get('default-query-string'))
        return click.decorators.argument('query', **attrs)(f)
    return decorator


def sort_option(**attrs):
    """Adds a ``sort`` argument as a decorator"""
    def decorator(f):
        attrs.setdefault('default', lambda: papis.config.get('sort-field'))
        attrs.setdefault('help', 'Sort documents with respect to FIELD')
        attrs.setdefault('metavar', 'FIELD')
        sort_f = click.decorators.option('--sort', "sort_field", **attrs)
        reverse_f = click.decorators.option(
            "--reverse", "sort_reverse",
            help="Reverse sort order", is_flag=True)
        return sort_f(reverse_f(f))
    return decorator


def doc_folder_option(**attrs):
    """Adds a ``query`` argument as a decorator"""
    def decorator(f):
        attrs.setdefault('default', None)
        attrs.setdefault('type', click.Path(exists=True))
        attrs.setdefault('help', 'Apply action to a document path')
        return click.decorators.option('--doc-folder', **attrs)(f)
    return decorator


def all_option(**attrs):
    """Adds a ``query`` argument as a decorator"""
    def decorator(f):
        attrs.setdefault('default', False)
        attrs.setdefault('is_flag', True)
        attrs.setdefault('help', 'Apply action to all matching documents')
        return click.decorators.option('-a', '--all', '_all', **attrs)(f)
    return decorator


def git_option(help="Add git interoperability", **attrs):
    """Adds a ``git`` option as a decorator"""
    def decorator(f):
        attrs.setdefault(
            'default',
            lambda: True if papis.config.get('use-git') else False)
        attrs.setdefault('help', help)
        return click.decorators.option('--git/--no-git', **attrs)(f)
    return decorator


def bypass(group, command, command_name):
    """
    This function is specially important for people developing scripts in
    papis.

    Suppose you're writing a plugin that uses the ``add`` command as seen
    in the command line in papis. However you don't want exactly the ``add``
    command and you want to add some behavior before calling it, and you
    don't want to write your own ``add`` function from scratch.

    You can then use the following snippet

    .. code::python

        import click
        import papis.cli
        import papis.commands.add

        @click.group()
        def main():
            \"\"\"Your main app\"\"\"
            pass

        @papis.cli.bypass(main, papis.commands.add.cli, "add")
        def add(**kwargs):
            # do some logic here...
            # and call the original add command line function by
            papis.commands.add.cli.bypassed(**kwargs)
    """
    group.add_command(command, command_name)

    def decorator(new_callback):
        setattr(command, "bypassed", command.callback)
        command.callback = new_callback
    return decorator
