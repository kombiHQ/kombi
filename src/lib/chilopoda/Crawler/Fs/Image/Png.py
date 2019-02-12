from .Oiio import Oiio

class Png(Oiio):
    """
    Png crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains an png file.
        """
        if not super(Png, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() == 'png'


# registration
Png.register(
    'png',
    Png
)
