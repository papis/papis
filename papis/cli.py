import click
import papis.config


def query_option(**attrs):
    """Adds a ``query`` argument as a decorator"""
    def decorator(f):
        attrs.setdefault(
            'default',
            lambda: papis.config.get('default-query-string'))
        return click.decorators.argument('query', **attrs)(f)
    return decorator


def doc_folder_option(**attrs):
    """Adds a ``query`` argument as a decorator"""
    def decorator(f):
        attrs.setdefault('default', None)
        attrs.setdefault('type', click.Path(exists=True))
        attrs.setdefault('help', 'Apply action to a document path')
        return click.decorators.option('--doc-folder', **attrs)(f)
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
