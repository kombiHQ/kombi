from .OiioCrawler import OiioCrawler

class TiffCrawler(OiioCrawler):
    """
    Tiff crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains an tiff file.
        """
        if not super(TiffCrawler, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() in ('tif', 'tiff')


# registration
TiffCrawler.register(
    'tiff',
    TiffCrawler
)
