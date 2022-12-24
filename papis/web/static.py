import os
from typing import List

import papis.config


def static_paths() -> List[str]:
    """
    This is the static directories where the papis web-application
    can access files.
    """
    return [
        os.path.join(papis.config.get_config_folder(),
                     "web")
    ]
