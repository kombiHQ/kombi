from ..Ascii import XmlElement

class LutElement(XmlElement):
    """
    Abstracted lut element.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a lut element.
        """
        super(LutElement, self).__init__(*args, **kwargs)

        self.setVar('category', 'lut')

        # setting a lut tag
        self.setTag(
            'lut',
            self.pathHolder().baseName()
        )
