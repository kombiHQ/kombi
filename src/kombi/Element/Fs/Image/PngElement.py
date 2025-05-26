from .OiioElement import OiioElement

class PngElement(OiioElement):
    """
    Png element.
    """

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains an png file.
        """
        if not super(PngElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] == 'png'


# registration
PngElement.register(
    'png',
    PngElement
)
