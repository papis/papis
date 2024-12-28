"""This module implements custom exceptions used to make the code more readable."""

import papis.strings


class DefaultSettingValueMissing(KeyError):
    """Exception raised when a configuration setting is missing and has no
    default value."""

    def __init__(self, key: str) -> None:
        message = f"""

    The configuration setting '{key}' is not defined.
    Try setting its value in your configuration file as such:

        [settings]
        {key} = some-value

    Don't forget to check the documentation.
        """
        super().__init__(message)


class DocumentFolderNotFound(FileNotFoundError):
    """Exception raised when a document has no main folder."""

    def __init__(self, doc: str) -> None:
        super().__init__(f"{papis.strings.no_folder_attached_to_document}: '{doc}'")
