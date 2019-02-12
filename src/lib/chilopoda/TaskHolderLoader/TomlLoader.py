from .PythonLoader import PythonLoader
from chilopodathirdparty import pytoml

class TomlLoader(PythonLoader):
    """
    Loads configuration from toml files.
    """

    @classmethod
    def parse(cls, contents):
        """
        Return parsed python data-structure from the input content.
        """
        return pytoml.loads(
            contents
        )


# registering task loader
TomlLoader.register(
    'toml',
    TomlLoader
)
