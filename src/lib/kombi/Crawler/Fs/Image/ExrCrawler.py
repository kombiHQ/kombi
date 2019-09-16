from .OiioCrawler import OiioCrawler

class ExrCrawler(OiioCrawler):
    """
    Exr crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains an exr file.
        """
        if not super(ExrCrawler, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() == 'exr'


# registration
ExrCrawler.register(
    'exr',
    ExrCrawler
)
