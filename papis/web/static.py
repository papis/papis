import os

import papis.config


def static_paths() -> list[str]:
    """
    This is the static directories where the Papis web-application
    can access files.
    """
    return [
        os.path.join(papis.config.get_config_folder(),
                     "web")
    ]
