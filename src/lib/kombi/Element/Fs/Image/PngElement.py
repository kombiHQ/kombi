from .OiioElement import OiioElement

class PngElement(OiioElement):
    """
    Png element.
    """

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains an png file.
        """
        if not super(PngElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() == 'png'


# registration
PngElement.register(
    'png',
    PngElement
)
