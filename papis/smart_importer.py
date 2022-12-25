import logging
from typing import List, Optional

import papis.importer
import papis.downloaders

Imp = papis.importer.Importer

LOGGER = logging.getLogger("smart-importer")


def get_matching_importer_or_downloader(matching_string: str) -> List[Imp]:

    importers = []  # type: List[Imp]
    _imps = papis.importer.get_importers()
    _downs = papis.downloaders.get_available_downloaders()
    _all_importers = list(_imps) + list(_downs)
    for importer_cls in _all_importers:
        LOGGER.debug("trying with importer %s", importer_cls)
        try:
            importer = importer_cls.match(
                matching_string)  # type: Optional[Imp]
        except Exception as e:
            LOGGER.error(e)
            continue
        if importer:
            LOGGER.info("%s matches %s", matching_string, importer.name)
            try:
                importer.fetch()
            except Exception as e:
                LOGGER.error(e)
            else:
                importers.append(importer)
    return importers


def guess_importers_from_strings(strings: List[str]) -> List[Imp]:
    """
    Guess which importers can be of use given a list of strings.
    """
    return sum((get_matching_importer_or_downloader(f)
                for f in strings),
               [])
