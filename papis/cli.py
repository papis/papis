import click
import os
import papis.config
import glob
import re


default_commands_path = os.path.join(os.path.dirname(__file__), 'commands')


def get_external_scripts():
    paths = []
    scripts = []
    paths.append(papis.config.get_scripts_folder())
    paths += os.environ["PATH"].split(":")
    for path in paths:
        scripts += glob.glob(os.path.join(path, "papis-*"))
    return scripts


def script_paths_to_dict(paths):
    scripts_dict = dict()
    for path in paths:
        command_name = (
            os.path.basename(path)
            .replace('papis-', '')
            .replace('.py', '')
        )
        scripts_dict[command_name] = dict(
            command_name=command_name,
            path=path,
            python=path.endswith(".py")
        )
    return scripts_dict


class MultiCommand(click.MultiCommand):

    scripts = script_paths_to_dict(
        list(filter(
            lambda path: not re.match(r'.*__init__.py$', path),
            glob.glob(os.path.join(default_commands_path, '*.py'))
        )) +
        get_external_scripts()
    )

    def list_commands(self, ctx):
        """List all matched commands in the command folder and in path

        >>> mc = MultiCommand()
        >>> rv = mc.list_commands(None)
        >>> len(rv) > 0
        True
        """
        rv = [s for s in self.scripts.keys()]
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        """Get the command to be run

        >>> mc = MultiCommand()
        >>> cmd = mc.get_command(None, 'add')
        >>> cmd.name, cmd.help
        ('add', 'Add...')
        >>> mc.get_command(None, 'this command does not exist')
        """
        namespace = {}
        try:
            script = self.scripts[name]
        except KeyError:
            return None
        if script['python']:
            with open(script['path']) as f:
                code = compile(f.read(), script['path'], 'exec')
                eval(code, namespace, namespace)
            if 'cli' in namespace.keys():
                return namespace['cli']
        # If it gets here, it means that it is an external script
        from papis.commands.external import external_cli as cli
        from papis.commands.external import get_command_help
        cli.context_settings['obj'] = script
        cli.help = get_command_help(script['path'])
        cli.name = script["command_name"]
        cli.short_help = cli.help
        return cli


def query_option(**attrs):
    """Adds a ``query`` argument as a decorator"""
    def decorator(f):
        import papis.config
        attrs.setdefault(
            'default',
            lambda: papis.config.get('default-query-string')
        )
        return click.decorators.argument('query', **attrs)(f)
    return decorator


def git_option(**attrs):
    """Adds a ``git`` option as a decorator"""
    def decorator(f):
        import papis.config
        attrs.setdefault(
            'default',
            lambda: True if papis.config.get('use-git') else False
        )
        attrs.setdefault('help', 'Add git interoperability')
        return click.decorators.option('--git/--no-git', **attrs)(f)
    return decorator


def bypass(group, command, command_name):
    """
    This function is specially important for people developing scripts in papis.

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
