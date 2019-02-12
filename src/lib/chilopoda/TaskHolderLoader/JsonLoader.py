import json
from .PythonLoader import PythonLoader

class JsonLoader(PythonLoader):
    """
    Loads configuration from json files.
    """

    @classmethod
    def parse(cls, contents):
        """
        Return parsed python data-structure from the input content.
        """
        return json.loads(
            contents
        )


# registering task loader
PythonLoader.register(
    'json',
    JsonLoader
)
