from .OiioCrawler import OiioCrawler

class DpxCrawler(OiioCrawler):
    """
    Dpx crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains an dpx file.
        """
        if not super(DpxCrawler, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() == 'dpx'


# registration
DpxCrawler.register(
    'dpx',
    DpxCrawler
)
