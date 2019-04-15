from .PythonLoader import PythonLoader

# in case pytoml is not available importing from third-party
try:
    import pytoml
except ImportError:
    from kombithirdparty import pytoml

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
