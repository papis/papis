import logging
import isbnlib
# See https://github.com/xlcnd/isbnlib for details

logger = logging.getLogger('papis:isbnlib')


def get_data(query="", service=None):
    global logger
    results = []
    logger.debug('Trying to retrieve isbn')
    isbn = isbnlib.isbn_from_words(query)
    data = isbnlib.meta(isbn, service=service)
    if data is None:
        return results
    else:
        logger.debug('Trying to retrieve isbn')
        assert(isinstance(data, dict))
        results.append(data_to_papis(data))
        return results


def data_to_papis(data):
    """Convert data from isbnlib into papis formated data

    :param data: Dictionary with data
    :type  data: dict
    :returns: Dictionary with papis keynames

    """
    data = {k.lower(): data[k] for k in data}
    return data
