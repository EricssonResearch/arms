"""Configuration storage."""

import json


class Container:
    """Load and store configurations.

    Attributes:
        data: configuration data (dict).
        error: error message (str).
    """

    def __init__(self):
        self.data = None
        self.error = "No error"
        self.load()

    def load(self):
        """Load configurations from file."""
        try:
            with open("arms/config/config.json", 'r') as stream:
                self.data = json.load(stream)
        except OSError as e:
            self.data = None
            self.error = "OSError - " + str(e)
        except ValueError as e:
            self.data = None
            self.error = "ValueError - " + str(e)


var = Container()
