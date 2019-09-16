from .OiioCrawler import OiioCrawler

class PngCrawler(OiioCrawler):
    """
    Png crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains an png file.
        """
        if not super(PngCrawler, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() == 'png'


# registration
PngCrawler.register(
    'png',
    PngCrawler
)
