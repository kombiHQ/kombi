import json
from .AsciiCrawler import AsciiCrawler

class JsonCrawler(AsciiCrawler):
    """
    Json crawler.
    """

    def _runParser(self):
        """
        Parse the json contents.
        """
        with open(self.var('filePath')) as f:
            return json.load(f)

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a json file.
        """
        if not super(AsciiCrawler, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() in ['json']


# registration
JsonCrawler.register(
    'json',
    JsonCrawler
)
