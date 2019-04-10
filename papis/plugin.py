import logging

logger = logging.getLogger("plugin")


def stevedore_error_handler(manager, entrypoint, exception):
    logger.error("Error while loading entrypoint [%s]" % entrypoint)
    logger.error(exception)
