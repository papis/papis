import click
import click.decorators
import os

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')


class MultiCommand(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        namespace = {}
        fn = os.path.join(plugin_folder, name + '.py')
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, namespace, namespace)
        if 'cli' in namespace.keys():
            return namespace['cli']
        else:
            return None


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


def pick(options, pick_config={}):
    import papis.api
    import papis.config
    import papis.utils
    if len(options) == 0:
        return None
    if not pick_config:
        header_format = papis.config.get("header-format")
        match_format = papis.config.get("match-format")
        pick_config = dict(
            header_filter=lambda x: papis.utils.format_doc(
                header_format, x
            ),
            match_filter=lambda x: papis.utils.format_doc(match_format, x)
        )
    return papis.api.pick(
        options,
        pick_config
    )
