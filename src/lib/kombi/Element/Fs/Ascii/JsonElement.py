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
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains a json file.
        """
        if not super(AsciiElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() in ['json']


# registration
JsonElement.register(
    'json',
    JsonElement
)
