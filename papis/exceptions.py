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
        message = """

    The configuration setting '{0}' is not defined.
    Try setting its value in your configuration file as such:

        [settings]
        {0} = some-value

    Don't forget to check the documentation.
        """.format(key)
        super(DefaultSettingValueMissing, self).__init__(message)
