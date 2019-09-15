from .PythonLoader import PythonLoader

# in case yaml is not available importing from third-party
try:
    import yaml
except ImportError:
    from kombithirdparty import yaml

class YamlLoader(PythonLoader):
    """
    Loads configuration from yaml files.
    """

    @classmethod
    def parse(cls, contents):
        """
        Return parsed python data-structure from the input content.
        """
        return yaml.load(
            contents
        )


# registering task loader
YamlLoader.register(
    'yaml',
    YamlLoader
)
