import os


def get_resource(name):
    path = os.path.join(os.path.dirname(__file__), 'resources', name)
    assert os.path.exists(path)
    with open(path) as f:
        return f.read()
