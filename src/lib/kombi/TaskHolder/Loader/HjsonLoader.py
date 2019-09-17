from .PythonLoader import PythonLoader

# in case hjson is not available importing from third-party
try:
    import hjson
except ImportError:
    from kombithirdparty import hjson

class HjsonLoader(PythonLoader):
    """
    Loads configuration from hjson files.
    """

    @classmethod
    def parse(cls, contents):
        """
        Return parsed python data-structure from the input content.
        """
        return hjson.loads(
            contents
        )


# registering task loader
PythonLoader.register(
    'hjson',
    HjsonLoader
)
