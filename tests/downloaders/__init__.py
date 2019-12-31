import os
import json


def get_resource(name):
    path = os.path.join(os.path.dirname(__file__), 'resources', name)
    assert os.path.exists(path)
    with open(path, errors='ignore') as f:
        return f.read()


def get_json_resource(name):
    return json.loads(get_resource(name))
