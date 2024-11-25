from .OiioElement import OiioElement

class TiffElement(OiioElement):
    """
    Tiff element.
    """

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains an tiff file.
        """
        if not super(TiffElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() in ('tif', 'tiff')


# registration
TiffElement.register(
    'tiff',
    TiffElement
)
