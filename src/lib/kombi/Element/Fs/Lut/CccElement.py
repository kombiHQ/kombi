from .LutElement import LutElement

class CccElement(LutElement):
    """
    Parses a Ccc file.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Ccc object.
        """
        super(CccElement, self).__init__(*args, **kwargs)

        try:
            self.__parseXML()
        except Exception as err:
            self.setVar('error', str(err))

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a lut file.
        """
        if not super(CccElement, cls).test(path, parentElement, ignoreExt=True):
            return False

        return path.suffix[1:] == 'ccc'

    def __parseXML(self):
        """
        Parse the ccc file (XML file format) information and assign that to the element.
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


# registering element
CccElement.register(
    'ccc',
    CccElement
)
