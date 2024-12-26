from .OiioElement import OiioElement

class TiffElement(OiioElement):
    """
    Tiff element.
    """

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains an tiff file.
        """
        if not super(TiffElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] in ('tif', 'tiff')


# registration
TiffElement.register(
    'tiff',
    TiffElement
)
