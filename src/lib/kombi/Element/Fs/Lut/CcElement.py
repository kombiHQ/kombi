from .LutElement import LutElement

class CcElement(LutElement):
    """
    Parses a Cc file.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Cc object.
        """
        super(CcElement, self).__init__(*args, **kwargs)

        try:
            self.__parseXML()
        except Exception as err:
            self.setVar('error', str(err))

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a lut file.
        """
        if not super(CcElement, cls).test(path, parentElement, ignoreExt=True):
            return False

        return path.suffix[1:] == 'cc'

    def __parseXML(self):
        """
        Parse the ccc file (XML file format) information and assign that to the element.
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


# registering element
CcElement.register(
    'cc',
    CcElement
)
