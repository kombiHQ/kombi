from ..Ascii import XmlInfoCrate

class LutInfoCrate(XmlInfoCrate):
    """
    Abstracted lut infoCrate.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a lut infoCrate.
        """
        super(LutInfoCrate, self).__init__(*args, **kwargs)

        self.setVar('category', 'lut')

        # setting a lut tag
        self.setTag(
            'lut',
            self.pathHolder().baseName()
        )
