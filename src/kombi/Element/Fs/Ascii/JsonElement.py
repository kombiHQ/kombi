import json
from .AsciiElement import AsciiElement

class JsonElement(AsciiElement):
    """
    Json element.
    """

    def _runParser(self):
        """
        Parse the json contents.
        """
        with open(self.var('filePath')) as f:
            return json.load(f)

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a json file.
        """
        if not super(AsciiElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] in ['json']


# registration
JsonElement.register(
    'json',
    JsonElement
)
