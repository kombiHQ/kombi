from .Oiio import Oiio

class Dpx(Oiio):
    """
    Dpx crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains an dpx file.
        """
        if not super(Dpx, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() == 'dpx'


# registration
Dpx.register(
    'dpx',
    Dpx
)
