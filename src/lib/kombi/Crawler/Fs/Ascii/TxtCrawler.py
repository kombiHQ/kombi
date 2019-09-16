from .AsciiCrawler import AsciiCrawler

class TxtCrawler(AsciiCrawler):
    """
    Txt crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a txt file.
        """
        if not super(AsciiCrawler, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() in ['txt']


# registration
TxtCrawler.register(
    'txt',
    TxtCrawler
)
