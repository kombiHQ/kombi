from .LutCrawler import LutCrawler

class CccCrawler(LutCrawler):
    """
    Parses a Ccc file.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Ccc object.
        """
        super(CccCrawler, self).__init__(*args, **kwargs)

        try:
            self.__parseXML()
        except Exception as err:
            self.setVar('error', str(err))

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a lut file.
        """
        if not super(CccCrawler, cls).test(pathHolder, parentCrawler, ignoreExt=True):
            return False

        return pathHolder.ext() == 'ccc'

    def __parseXML(self):
        """
        Parse the ccc file (XML file format) information and assign that to the crawler.
        """
        tags = ['Slope', 'Offset', 'Power', 'Saturation']
        requireTags = ['ColorCorrection', 'ColorCorrectionCollection']

        # Check if the cdl have the required tags
        for tag in requireTags:
            self.queryTag(tag)

        # Get the values from the cdl file
        for tag in tags:
            tagValue = self.queryTag(tag)
            if tag == 'Saturation':
                self.setVar(tag.lower(), float(tagValue[0]))
                continue

            value = list(map(float, tagValue[0].split(" ")))
            self.setVar(tag.lower(), value)


# registering crawler
CccCrawler.register(
    'ccc',
    CccCrawler
)
