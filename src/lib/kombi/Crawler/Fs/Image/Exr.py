from .Oiio import Oiio

class Exr(Oiio):
    """
    Exr crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains an exr file.
        """
        if not super(Exr, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() == 'exr'


# registration
Exr.register(
    'exr',
    Exr
)
