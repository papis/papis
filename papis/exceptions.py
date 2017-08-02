"""This module implements custom exceptions used to make the code more
readable.
"""


class SettingNotRegistered(Exception):
    """This exception is when a setting is to be retrieved that has not been
    considered beforehand in the code and registered accordingly, thus giving a
    default value to it"""
    pass


class DefaultSettingValueMissing(Exception):
    """This exception is when a setting's value has no default value.
    """

    def __init__(self, key):
        message = "\nValue for '%s' is not at all registered and known" % (key)
        super(DefaultSettingValueMissing, self).__init__(message)
