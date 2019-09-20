from kombi.Crawler.Fs.Image import PngCrawler
from kombi.Crawler.VarExtractor import VarExtractor

class VendorXPngPlate(PngCrawler):
    """
    Implements a custom vendor "X" png plate crawler.

    Alternatively you can use inline crawlers instead of this implementation,
    please check the example: vendorXPlatesInlineCrawlers
    """

    # name example: "foo_def_abc_foo_001.0001.png"
    namePattern = "{job:3}_{shot:3}_{seq:3}_{plateName}_{vendorVersion:3i}.####.png"

    def __init__(self, *args, **kwargs):
        """
        Create a vendor "X" png plate crawler.
        """
        super(VendorXPngPlate, self).__init__(*args, **kwargs)

        # assigning variables
        self.assignVars(
            VarExtractor(
                self.var('baseName'),
                self.namePattern
            )
        )

        # setting context variables
        self.setVar(
            'vendorVersion',
            self.var('vendorVersion'),
            isContextVar=True
        )

        self.setVar(
            'plateName',
            self.var('plateName'),
            isContextVar=True
        )

    @classmethod
    def test(cls, data, parentCrawler=None):
        """
        Return a boolean telling if the input data can become a vendor "x" png plate crawler.
        """
        # perform the tests for the base classes
        if super(VendorXPngPlate, cls).test(data, parentCrawler):
            return VarExtractor(data.baseName(), cls.namePattern).match()

        return False


# registering crawler
PngCrawler.register(
    'vendorXPngPlate',
    VendorXPngPlate
)
