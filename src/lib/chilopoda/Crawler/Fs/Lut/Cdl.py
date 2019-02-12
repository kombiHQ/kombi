from .Lut import Lut

class Cdl(Lut):
    """
    Parses a cdl file.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Cdl object.
        """
        super(Cdl, self).__init__(*args, **kwargs)

        self.__parseXML()

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a cdl file.
        """
        return pathHolder.ext() == 'cdl'

    def __parseXML(self):
        """
        Parse the cld file (XML file format) information and assign that to the crawler.
        """
        cdlTags = ['Slope', 'Offset', 'Power', 'Saturation']
        cdlRequireTags = ['ColorCorrection', 'ColorDecision', 'ColorDecisionList']

        # Check if the cdl have the required tags
        for tag in cdlRequireTags:
            self.queryTag(tag)

        # Get the values from the cdl file
        for tag in cdlTags:
            tagValue = self.queryTag(tag)
            if tag == 'Saturation':
                self.setVar(tag.lower(), float(tagValue[0]))
                continue

            value = list(map(float, tagValue[0].split(" ")))
            self.setVar(tag.lower(), value)


# registering crawler
Cdl.register(
    'cdl',
    Cdl
)
