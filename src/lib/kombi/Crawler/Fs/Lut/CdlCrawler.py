from .LutCrawler import LutCrawler

class CdlCrawler(LutCrawler):
    """
    Parses a cdl file.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a cdl object.
        """
        super(CdlCrawler, self).__init__(*args, **kwargs)

        try:
            self.__parseXML()
        except Exception as err:
            self.setVar('error', str(err))

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a cdl file.
        """
        if not super(CdlCrawler, cls).test(pathHolder, parentCrawler, ignoreExt=True):
            return False

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
CdlCrawler.register(
    'cdl',
    CdlCrawler
)
