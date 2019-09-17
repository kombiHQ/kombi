from .OiioCrawler import OiioCrawler

class JpgCrawler(OiioCrawler):
    """
    Jpg crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains an jpg file.
        """
        if not super(JpgCrawler, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() == 'jpg'


# registration
JpgCrawler.register(
    'jpg',
    JpgCrawler
)
