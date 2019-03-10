from ..Ascii import Ascii

class Txt(Ascii):
    """
    Txt crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a txt file.
        """
        if not super(Ascii, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() in ['txt']


# registration
Txt.register(
    'txt',
    Txt
)
