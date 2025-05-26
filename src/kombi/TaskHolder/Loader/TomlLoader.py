from .PythonLoader import PythonLoader

class TomlLoader(PythonLoader):
    """
    Loads configuration from toml files.
    """

    @classmethod
    def parse(cls, contents):
        """
        Return parsed python data-structure from the input content.
        """
        # third-party dependency
        import pytoml

        return pytoml.loads(
            contents
        )


# registering task loader
TomlLoader.register(
    'toml',
    TomlLoader
)
