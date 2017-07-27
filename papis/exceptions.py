"""This module implements custom exceptions used to make the code more
readable.
"""


class NotImplemented(Exception):
    """This exception is to be used when something throughout the code is not
    yet implemented.  """
    pass


class SettingNotRegistered(object):
    """This exception is when a setting is to be retrieved that has not been
    considered beforehand in the code and registered accordingly, thus giving a
    default value to it"""
    pass


class DefaultSettingValueMissing(object):
    """This exception is when a setting's value has no default value.
    """
    pass
