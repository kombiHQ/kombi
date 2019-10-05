from .LutCrawler import LutCrawler

class CcCrawler(LutCrawler):
    """
    Parses a Cc file.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Cc object.
        """
        super(CcCrawler, self).__init__(*args, **kwargs)

        self.__parseXML()

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a lut file.
        """
        if not super(CcCrawler, cls).test(pathHolder, parentCrawler, ignoreExt=True):
            return False

        return pathHolder.ext() == 'cc'

    def __parseXML(self):
        """
        Parse the ccc file (XML file format) information and assign that to the crawler.
        """
        tags = ['Slope', 'Offset', 'Power', 'Saturation']
        requireTags = ['ColorCorrection']

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
CcCrawler.register(
    'cc',
    CcCrawler
)
