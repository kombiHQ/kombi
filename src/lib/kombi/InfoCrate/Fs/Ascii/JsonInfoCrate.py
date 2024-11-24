import json
from .AsciiInfoCrate import AsciiInfoCrate

class JsonInfoCrate(AsciiInfoCrate):
    """
    Json infoCrate.
    """

    def _runParser(self):
        """
        Parse the json contents.
        """
        with open(self.var('filePath')) as f:
            return json.load(f)

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains a json file.
        """
        if not super(AsciiInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        return pathHolder.ext() in ['json']


# registration
JsonInfoCrate.register(
    'json',
    JsonInfoCrate
)
