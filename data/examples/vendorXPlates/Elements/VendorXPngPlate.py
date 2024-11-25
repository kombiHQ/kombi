from kombi.Element.Fs.Image import PngElement
from kombi.Element.VarExtractor import VarExtractor

class VendorXPngPlate(PngElement):
    """
    Implements a custom vendor "X" png plate element.

    Alternatively you can use inline elements instead of this implementation,
    please check the example: vendorXPlatesInlineElements
    """

    # name example: "foo_def_abc_foo_001.0001.png"
    namePattern = "{job:3}_{shot:3}_{seq:3}_{plateName}_{vendorVersion:3i}.####.png"

    def __init__(self, *args, **kwargs):
        """
        Create a vendor "X" png plate element.
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
    def test(cls, data, parentElement=None):
        """
        Return a boolean telling if the input data can become a vendor "x" png plate element.
        """
        # perform the tests for the base classes
        if super(VendorXPngPlate, cls).test(data, parentElement):
            return VarExtractor(data.baseName(), cls.namePattern).match()

        return False


# registering element
PngElement.register(
    'vendorXPngPlate',
    VendorXPngPlate
)
