from ..Ascii import XmlCrawler

class LutCrawler(XmlCrawler):
    """
    Abstracted lut crawler.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a lut crawler.
        """
        super(LutCrawler, self).__init__(*args, **kwargs)

        self.setVar('category', 'lut')

        # setting a lut tag
        self.setTag(
            'lut',
            self.pathHolder().baseName()
        )
