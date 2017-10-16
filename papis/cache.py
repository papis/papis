import logging
import os
import papis.utils
import papis.config


logger = logging.getLogger("cache")


def get_folder():
    """Get folder where the cache files are stored, it retrieves the
    ``cache-dir`` configuration setting. It is ``XDG`` standard compatible.
    """
    return os.path.expanduser(papis.config.get('cache-dir'))


def get(path):
    """Get contents stored in a cache file ``path`` in pickle binary format.

    :param path: Path to the cache file.
    :type  path: str
    :returns: Content of the cache file.
    :rtype: object
    """
    import pickle
    logger.debug("Getting cache %s " % path)
    return pickle.load(open(path, "rb"))


def create(obj, path):
    """Create a cache file in ``path`` with obj as its content using pickle
    binary format.

    :param obj: Any seriazable object.
    :type  obj: object
    :param path: Path to the cache file.
    :type  path: str
    :returns: Nothing
    :rtype: None
    """
    import pickle
    logger.debug("Saving in cache %s " % path)
    pickle.dump(obj, open(path, "wb+"))


def get_name(directory):
    """Create a cache file name out of the path of a given directory.

    :param directory: Folder name to be used as a seed for the cache name.
    :type  directory: str
    :returns: Name for the cache file.
    :rtype:  str
    """
    import hashlib
    return hashlib\
           .md5(directory.encode())\
           .hexdigest()+"-"+os.path.basename(directory)


def clear(directory):
    """Clear cache associated with a directory

    :param directory: Folder name that was used as a seed for the cache name.
    :type  directory: str
    :returns: Nothing
    :rtype: None
    """
    directory = os.path.expanduser(directory)
    cache_name = get_name(directory)
    cache_path = os.path.join(get_folder(), cache_name)
    if os.path.exists(cache_path):
        logger.debug("Clearing cache %s " % cache_path)
        os.remove(cache_path)


def clear_lib_cache(lib=None):
    """Clear cache associated with a library. If no library is given
    then the current library is used.

    :param lib: Library name.
    :type  lib: str
    """
    directory = papis.config.get("dir", section=lib)
    clear(directory)


def get_folders(directory):
    """Get folders from within a containing folder from cache

    :param directory: Folder to look for documents.
    :type  directory: str
    :param search: Valid papis search
    :type  search: str
    :returns: List of document objects.
    :rtype: list
    """
    cache = get_folder()
    cache_name = get_name(directory)
    cache_path = os.path.join(cache, cache_name)
    folders = []
    logger.debug("Getting documents from dir %s" % directory)
    logger.debug("Cache path = %s" % cache_path)
    if not os.path.exists(cache):
        logger.debug("Creating cache dir %s " % cache)
        os.makedirs(cache, mode=papis.config.getint('dir-umask'))
    if os.path.exists(cache_path):
        logger.debug("Loading folders from cache")
        folders = get(cache_path)
    else:
        folders = papis.utils.get_folders(directory)
        create(folders, cache_path)
    return folders
