from .PythonLoader import PythonLoader

class YamlLoader(PythonLoader):
    """
    Loads configuration from yaml files.
    """

    @classmethod
    def parse(cls, contents):
        """
        Return parsed python data-structure from the input content.
        """
        # third-party dependency
        import yaml

        return yaml.load(
            contents,
            yaml.Loader
        )


# registering task loader
YamlLoader.register(
    'yaml',
    YamlLoader
)
